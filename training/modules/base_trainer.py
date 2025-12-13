import os
from types import SimpleNamespace
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class BaseTrainer:
    """Shared functionality for all trainers."""
    def __init__(self, config: dict):
        self.config = SimpleNamespace(**config)
        self.model = None
        self.tokenizer = None
        self.download_base_model()

    def download_base_model(self):
        """Downloads provided base model and save it to specific spot."""

        os.makedirs(self.config.save_dir + "/uno", exist_ok=True)

        if os.path.exists(self.config.save_dir + f"/uno-agent-agent-base-{self.config.model_id}"):
            print("Base model already exists. Skipping download")
            return

        print("DOWNLOADING BASE MODEL")

        # you do not need to train the tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model, use_fast=False
        )
        self.tokenizer.save_pretrained(self.config.save_dir + f"/tokenizer-{self.config.model_id}")

        model = AutoModelForSeq2SeqLM.from_pretrained(
            self.config.base_model, device_map="auto"
        )
        model.save_pretrained(self.config.save_dir + f"/uno-agent-base-{self.config.model_id}")

    # def save_info(self):
    #     # TODO this will be used after training so that we can reproduce results
    #     config_log = {
    #         "base_model": self.base_model,
    #         "training_args": training_args.to_dict(),
    #         "peft_config": peft_config.to_dict(),
    #         "train_data": train_data_fp,
    #         "test_ratio": test_ratio,
    #         "seed": self.seed
    #     }

    #     with open(self.save_dir + f"/uno/training-log-{self.model_id}.json", 'w') as f:
    #         json.dump(config_log, f, indent=2)
