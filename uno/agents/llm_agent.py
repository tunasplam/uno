from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from .agent import Agent

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

    def act(self, prompt_dict: dict, is_turn: bool) -> str:
        prompt = self._build_prompt(prompt_dict)

        inputs = self.tokenizer(
            prompt, return_tensors="pt"
        ).to(self.model.device)

        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=20,
            do_sample=False,
            num_beams=1, #greedy alg
            temperature=1.0
        )

        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return response

    def _build_prompt(self, prompt: dict) -> str:
        system_parts = []

        for k in ("rules", "instructions", "strategy"):
            if k in prompt:
                system_parts.append(prompt[k])

        system_parts.append(f"{'\n'.join(prompt['context'])}s")
        system_parts.append("Question: Which card should you play?")
        system_parts.append("Answer:")
        return "\n".join(system_parts).strip()
