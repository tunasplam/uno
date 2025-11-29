"""This class represents each agent which will be playing multiple games of uno.
All agent-specific material is tracked here but game-specific information is tracked
in Player object.

Using llama-cpp-python + quantized 7B model at first with CPU. Eventually will want
to move towards GPU for speed.
"""

import logging
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class Agent:
    "MetaType for all agents."
    def act(self, prompt_dict: dict) -> dict:
        raise NotImplementedError

class LLMAgent(Agent):
    "These are LLMs playing the game."
    def __init__(self,strategy: str=None):

        self.tokenizer = AutoTokenizer.from_pretrained(
            "/home/jordan/agents/tokenizer",
            use_fast=False
        )

        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            "/home/jordan/agents/uno-agent"
        )

        self.strategy = strategy if strategy else "Do what you need to do to win the game."

    def act(self, prompt_dict: dict) -> str:
        prompt = self._build_prompt(prompt_dict)
        inputs = self.tokenizer(
            prompt, return_tensors="pt").to(self.model.device)
        output_ids = self.model.generate(**inputs, max_new_tokens=50)
        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        logging.info("RESPONSE:\n %s", response)
        return response

    def _build_prompt(self, prompt: dict) -> str:
        system_parts = []

        for k in ("rules", "instructions", "strategy"):
            if k in prompt:
                system_parts.append(prompt[k])

        system_parts.append(f"{'\n'.join(prompt['context'])}s")
        return "\n".join(system_parts).strip()

class HumanAgent(Agent):
    "For when humans want to play the game."
    def __init__(self):
        raise NotImplementedError

    def act(self, prompt_dict: dict) -> dict:
        raise NotImplementedError
