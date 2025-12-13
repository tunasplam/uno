from datasets import Dataset, load_dataset
from peft import LoraConfig, TaskType, get_peft_model
from torchinfo import summary
from transformers.trainer import Trainer, TrainingArguments
from transformers import (
    AutoTokenizer, DataCollatorForSeq2Seq, EarlyStoppingCallback, AutoModelForSeq2SeqLM
)
from .base_trainer import BaseTrainer

class SupervisedFineTuning(BaseTrainer):
    """Performs supervised fine-tuning on a pretrained model."""
    def __init__(self, config: dict):
        self.model = None
        self.tokenizer = None
        super().__init__(config)

    def train(self, train_data_fp: str, test_ratio: float = 0.1):
        """The goal here is to load a base model and teach it the rules of uno.
        When SFT is done then we should be able to have several AI agents complete
        a game of uno. The games do not need to be well played, then only need to
        be valid.
        """
        model = self._create_model()
        training_args = self._config_training_args()
        train_data, test_data = self._load_and_split_data(train_data_fp, test_ratio)
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_data,
            eval_dataset=test_data,
            data_collator=self._create_data_collator(model),
            callbacks=[EarlyStoppingCallback(
                # stop if no improvements for 3 epochs.
                early_stopping_patience=3
            )]
            # compute_metrics=self._compute_metrics # TODO this is optional. add later if need be
        )
        trainer.train()

        # TODO append all of these arguments to some sort of log for reproduction

        model.save_pretrained(self.config.save_dir + f"/uno-agent-fine-tuned-{self.config.model_id}")

    def _create_model(self):
        model = AutoModelForSeq2SeqLM.from_pretrained(
            self.config.save_dir + f"/uno-agent-base-{self.config.model_id}"
        )

        # TODO QLoRA? should try and use that if possible
        peft_config = LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM,
            inference_mode=False,
            r=4,  # Reduce from 8
            lora_alpha=16,  # Reduce from 32
            lora_dropout=0.05,
            target_modules=["q", "v"],  # Explicitly specify which modules
            bias="none",
            modules_to_save=None,
        )
        model = get_peft_model(model, peft_config)
        model.train()
        model.print_trainable_parameters()
        summary(model)
        return model

    def _config_training_args(self):
        """
        If your model is struggling to adapt to its task:
        - increase peak learning rate (if stable, i.e. grad_norm not diverging to inf)
        - train more (more epochs)
        - more training data or augment the data
        - less regularization
            weight_decay=0.0,
            dropout_rate=0.1,

        The goal is to minimize our loss function while avoiding overfitting.
        Loss should be decreasing (of plateauing) and should not experience
        any random spikes. grad_norm should also consistently be below 10.

        We want to target loss values between 1.00 and .50 for this application. Anything lower than .50
        should be checked for overfitting.

        After training, we evaluate the model and look at evaluation loss (test set). We should not see a large
        discrepancy between training loss and evaluation loss. If we do, we are overfitting.

        """
        return TrainingArguments(
            output_dir=self.config.save_dir + f"/uno-agent-fine-tuned-{self.config.model_id}",
            # we are fine-tuning a model that is already trained. thus, very small learning rates.
            # think of these as taking "fine brush, detailed adjustments" rather than using a sledgehammer.
            learning_rate=1e-5,

            # "learn slowly at first, then ramp up to full speed." Think of this like the choke on a carb. Training
            # may "sputter" if its "cold" (or learning something very unfamiliar).
            warmup_ratio=0.1,
            # after model is warmed up learning rate to decreases to 0 (at which point model tuning is done).
            # Different strategies can be used.
            # slow your decay (try cosine) if loss is still improving at end fo training but training is ending.
            # raise decay rate if training is stable but loss is not being affected.
            lr_scheduler_type="linear",

            num_train_epochs=1,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            weight_decay=0.01,

            # TODO this is incredibly conservative for VRAM. Ramp up later.
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=8,  # Simulate larger batch
            # grad_norm tells what direction and magnitude to update weights (calc III norm)
            # gradient clipping. avoids gradient diverging to infinity.
            max_grad_norm=1.0,
            save_steps=500,
            eval_steps=500,
            save_total_limit=2,  # Keep only 2 checkpoints
            optim="adamw_torch",

            # hooks up to tensorboard dashboard
            logging_dir=self.config.save_dir + f"/logs-{self.config.model_id}",
            # controls how often to log. i.e. 10 means every 10th step spawns a log entry.
            logging_steps=10,
            report_to="tensorboard"
        )

    def _create_data_collator(self, model) -> DataCollatorForSeq2Seq:
        """These form batches by using a list of dataset elements as input. Here we pass
        the tokenizer so that it applies tokenization to the batches for us.
        """
        if not self.tokenizer:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.save_dir + f"/uno-agent-tokenizer-{self.config.model_id}"
            )

        return DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=model
        )

    def _load_and_split_data(self, train_data_fp: str, test_ratio: float) -> tuple[Dataset, Dataset]:
        dataset = load_dataset(
            'json',
            data_files=train_data_fp,
            field="data" # since all of our data is listed under "data" key
        )

        def preprocess_function(examples: dict):
            """
            Examples is list of dicts with keys 'input' and 'output'
            Examples['input'] is list of strings. Same as examples['output']
            """
            # T5 expects "input" to be tokenized as inputs
            # and "output" to be tokenized as labels
            model_inputs = self.tokenizer(
                str(examples['input']),
                max_length=512,
                truncation=True,
                padding=False  # padding handled by collator
            )

            # Tokenize targets (outputs, in this case "the proper action")
            labels = self.tokenizer(
                str(examples['output']),
                max_length=512,
                truncation=True,
                padding=False
            )

            model_inputs['labels'] = labels['input_ids']
            return model_inputs

        tokenized_dataset = dataset['train'].map(
            preprocess_function,
            batched=False,
            remove_columns=dataset['train'].column_names
        )

        split_dataset = tokenized_dataset.train_test_split(test_size=test_ratio)
        return split_dataset['train'], split_dataset['test']
