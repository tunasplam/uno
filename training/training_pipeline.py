"""
The goal of this pipeline is to produce agents that are able to play games of uno
with suggested strategies.

- start with base models
- use supervised fine-tuning to teach the agents how to play valid games of uno
- use reinforcement learning to have them learn how to play well

Will probably want to save each phase in local spots and whatnot. And also document
what went into creating each so that we can replicate results.
uv
"""

from transformers import set_seed
from modules.sft import SupervisedFineTuning
from modules.rl import ReinforcementLearning

class UnoTrainingPipeline:
    def __init__(
            self, config: dict, seed: int=24
    ):
        self.tokenizer = None
        self.config = config
        self.checkpoints = {}
        set_seed(seed)
        self.sft = SupervisedFineTuning(config=self.config)
        self.rl = ReinforcementLearning(config=self.config)

    def supervised_fine_tuning(self, dataset_path: str, test_ratio: float=0.1):
        self.sft.train(dataset_path, test_ratio)

    def reinforcement_learning(self, iterations: int=100):
        self.rl.train(iterations)

if __name__ == '__main__':
    pipeline = UnoTrainingPipeline(
        {
            "base_model": "google/flan-t5-base",
            "save_dir": "/home/jordan/agents/uno",
            "model_id": "test2"
        }
    )
    pipeline.supervised_fine_tuning('autoset2k_v1.json')
