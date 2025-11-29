"""
Here we can manually trigger some games of uno
"""

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from uno import UnoServer, LLMAgent, HumanAgent

# four agents play a game
def play_one_game(num_agents: int=4):
    print("Creating agents...")
    agents = [HumanAgent(str(i)) for i in range(num_agents)]
    print("Creating server...")
    server = UnoServer(agents)
    print("Starting game...")
    server.play_game()
    print("Game over!")
    for p in server.players:
        print(f"Player {p.id} {p.result}")

def download_models():
    tokenizer = AutoTokenizer.from_pretrained(
        "google/flan-t5-base", use_fast=False
    )
    tokenizer.save_pretrained("/home/jordan/agents/tokenizer")

    model = AutoModelForSeq2SeqLM.from_pretrained(
        "google/flan-t5-base",
        device_map="auto"
    )
    model.save_pretrained("/home/jordan/agents/uno-agent")

# TODO we need training data. Let's generate it by playing games of uno. This means that we need to implement human agent
# and implement a logging strategy.
# training data needs to be of form:
# training_+data = [
#   {
    # "input": str,
    # "output": str
#   } ...
# we need at least 2000 examples. holy crap! maybe we generate programmatically?

if __name__ == '__main__':
    # TODO check if LLMs installed? if not, then call download_models?
    # download_models()
    play_one_game()
