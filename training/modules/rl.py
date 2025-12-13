from .base_trainer import BaseTrainer

class ReinforcementLearning(BaseTrainer):
    """Allows models to learn Uno strategy."""
    def __init__(self, config: dict):
        self.model = None
        self.tokenizer = None
        super().__init__(config)

    def train(self, iterations: int=1000):
        pass
