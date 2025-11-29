"""
Here we can manually trigger some games of uno
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from uno import UnoServer, LLMAgent

# four agents play a game
def play_one_game(num_agents: int=4):
    print("Creating agents...")
    agents = [LLMAgent() for _ in range(num_agents)]
    print("Creating server...")
    server = UnoServer(agents)
    print("Starting game...")
    server.play_game()
    print("Game over!")
    for p in server.players:
        print(f"Player {p.id} {p.result}")

def download_llama_models():
    tokenizer = AutoTokenizer.from_pretrained(
        "huggyllama/llama-7b", use_fast=False
    )
    tokenizer.save_pretrained("/home/jordan/agents/tokenizer")

    model = AutoModelForCausalLM.from_pretrained(
        "huggyllama/llama-7b",
        dtype=torch.float16,
        device_map="auto",
        attn_implementation="sdpa"
    )
    model.save_pretrained("/home/jordan/agents/uno-agent")

if __name__ == '__main__':
    # TODO check if LLMs installed? if not, then call download_llama_models?
    play_one_game()
