"""This class represents each agent which will be playing multiple games of uno.
All agent-specific material is tracked here but game-specific information is tracked
in Player object.

Using llama-cpp-python + quantized 7B model at first with CPU. Eventually will want
to move towards GPU for speed.
"""

import json
import logging

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# TODO:
# - we can also add memory here
# - maybe long-term agent identity?
# - agents need to keep track of the results from previous games

class Agent:
    "MetaType for all agents."
    def act(self, prompt_dict: dict) -> dict:
        raise NotImplementedError

class LLMAgent(Agent):
    "These are LLMs playing the game."
    def __init__(self,
        strategy: str=None,
        load_in_8bit: bool=False,
        load_in_4bit: bool=False
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # try loading agents from local storage first
        self.tokenizer = AutoTokenizer.from_pretrained(
            "/home/jordan/agents/tokenizer",
            use_fast=False
        )

        model_kwargs = self._prepare_kwargs(load_in_4bit, load_in_8bit)
        self.model = AutoModelForCausalLM.from_pretrained(
            "/home/jordan/agents/uno-agent",
            **model_kwargs
        )

        self.strategy = strategy if strategy else "Do what you need to do to win the game."

    def _prepare_kwargs(self, load_in_4bit: bool, load_in_8bit:bool) -> dict:
        model_kwargs = {
            "low_cpu_mem_usage": True,
        }
        
        if self.device == "cuda":
            # Use bfloat16 if available (faster than float16 on modern GPUs)
            if torch.cuda.is_bf16_supported():
                logging.info("Using bfloat16 for faster inference")
                model_kwargs["dtype"] = torch.bfloat16
            else:
                logging.info("Using float16")
                model_kwargs["dtype"] = torch.float16

            # Quantization options
            if load_in_4bit:
                logging.info("Loading model in 4-bit (slowest but most memory efficient)")
                model_kwargs["load_in_4bit"] = True
                
            elif load_in_8bit:
                logging.info("Loading model in 8-bit (balanced)")
                model_kwargs["load_in_8bit"] = True
            else:
                logging.info("Loading model in full precision (fastest)")

            model_kwargs["device_map"] = "auto"

        else:
            logging.warning("Running on CPU - inference will be slow!")
            model_kwargs["dtype"] = torch.float32
        
        return model_kwargs

    def act(self, prompt_dict: dict) -> dict:
        prompt = self._build_prompt(prompt_dict)
        #logging.info(prompt)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        output_ids = self.model.generate(**inputs, max_new_tokens=200)
        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return json.loads(response)

    def _build_prompt(self, prompt: dict) -> str:
        system_parts = []

        for k in ("rules", "instructions", "strategy"):
            if k in prompt:
                system_parts.append(f"=== {k.upper()} ===\n{prompt[k]}\n")

        system_parts.append(f"Current Context:\n{'\n'.join(prompt['context'])}\n")
        return "<s>[INST] <<SYS>>\n" + "\n".join(system_parts).strip()

class HumanAgent(Agent):
    "For when humans want to play the game."
    def __init__(self):
        raise NotImplementedError

    def act(self, prompt: dict) -> dict:
        raise NotImplementedError
