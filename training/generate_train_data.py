from functools import reduce
import json
from math import ceil
import operator
import random

import numpy as np
import uno

def generate_training_data(n: int, out: str, seed: int=24, ratios: dict=None):
    """Generates training data for our agents to learn from.

    Args:
        n (int): Number of samples to generate.
        out (str): Filename for json output
        seed (int, optional): What seed to use. Defaults to 24.
        ratios (dict, optional): Custom ratios for each scenario.
    """
    random.seed(seed)
    np.random.seed(seed)

    if not ratios:
        ratios = {
            "draw_needed_forced": .10,
            "draw_needed_no_playable": .15,
            "draw_unneeded": .05,

            "play_regular_symbol": .25,
            "play_regular_color": .25,
            "play_wild_change": .08,
            "play_wild_same": .02,

            "uno_defense": .05,
            "uno_offense": .05
        }

    if sum(ratios.values()) != 1:
        raise ValueError("Ratios must add to 1.")

    # generate scenarios
    data: list[dict] = reduce(
        operator.add,
        (generate_data_for_key(k, ceil(r*n)) for k, r in ratios.items())
    )

    # TODO configure where to save training data
    with open(f"training/{out}.json", 'w', encoding="utf-8") as f:
        json.dump({"data": data[:n]}, f)

def generate_data_for_key(k: str, n: int) -> list[dict]:
    # Check if an input key is valid. If so, map it to correct function
    # and invoke.
    allowed_entries = {
        "draw_needed_forced": draw_needed_forced,
        "draw_needed_no_playable": draw_needed_no_playable,
        "draw_unneeded": draw_unneeded,
        "play_regular_symbol": play_regular_symbol,
        "play_regular_color": play_regular_color,
        "play_wild_change": play_wild_change,
        "play_wild_same": play_wild_same,
        "uno_defense": uno_defense,
        "uno_offense": uno_offense
    }
    if k not in allowed_entries:
        raise ValueError(f"Invalid key {k} in ratios.")

    f = allowed_entries[k]
    return [f() for _ in range(n)]

def create_input(server: uno.UnoServer, p: uno.Player) -> str:
    "Abstracts away some nastiness"
    return p.agent.build_prompt(
        p.create_prompt(
            server.build_context(server.next_player, True)
            )
        )

# for each of these scenarios, generate a random game state
# and then apply custom requirements.

def draw_needed_forced() -> dict:
    server = random_game_state()

    # if a player has one card, they must be shielded.
    for p in server.players:
        if len(p.hand) == 1:
            p.is_shielded = True

    # set top card to be a card which forces draws
    server.deck.discard_pile[-1] = random.choice([
        'WF', 'DR', 'DY', 'DG', 'DB'
    ])

    # set current player must_draw to a number
    if uno.is_wild(server.deck.top_card_on_discard_pile()):
        server.must_draw_count = random.randint(1,4)
    else:
        server.must_draw_count = random.randint(1,2)

    return {
        "input": ''.join(create_input(server, server.next_player)),
        "output": {"action": "Draw card"}
    }

def draw_needed_no_playable() -> list[dict]:
    return

def draw_unneeded() -> list[dict]:
    return

def play_regular_symbol() -> list[dict]:
    return

def play_regular_color() -> list[dict]:
    return

def play_wild_change() -> list[dict]:
    return

def play_wild_same() -> list[dict]:
    return

def uno_defense() -> list[dict]:
    # do when one card and unshielded
    return

def uno_offense() -> list[dict]:
    # do when player has one card
    return

def random_game_state() -> uno.UnoServer:
    # generate a random number of players
    n_players = random.randint(2,6)
    # agents are only used to generate relevant prompts
    s = "Do what you need to do to win"
    agents = [uno.LLMAgent(strategy=s) for _ in range(n_players)]
    server = uno.UnoServer(agents, blank_slate=True)

    # give a random number of cards to each player.
    # using poisson bc of shape and discrete data.
    # no one may have 0 cards.
    for p in server.players:
        n_cards = max(np.random.poisson(lam=5),1)
        for _ in range(n_cards):
            p.give(server.deck.draw())

    # then randomly split leftover cards between discard pile and deck.
    split_point = random.randint(1,len(server.deck.cards))
    for _ in range(split_point):
        server.deck.discard_pile.append(
            server.deck.draw()
        )
    return server

if __name__ == '__main__':
    # from pprint import pprint
    # pprint(generate_data_for_key("draw_needed_forced", 10))
    generate_training_data(10, 'test')
