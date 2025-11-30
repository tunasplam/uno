from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
import json
from math import ceil
import random
from typing import get_args

import numpy as np
from tqdm import tqdm
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
            "play_wild": .1,

            "uno_defense": .05,
            "uno_offense": .05
        }

    if sum(ratios.values()) != 1:
        raise ValueError("Ratios must add to 1.")

    data: list[dict] = []

    # generate scenarios
    with ProcessPoolExecutor() as executor:
        # submit all tasks
        futures = {
            executor.submit(generate_data_for_key, k, ceil(r*n)): k
            for k, r in ratios.items()
        }

        # collect results are they complete
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Generating train set data."
        ):
            data.extend(future.result())

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
        "play_wild": play_wild,
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

def random_card_no_wild() -> uno.Card:
    "DOES NOT RETURN WILD CARDS"
    return random.choice(get_args(uno.Color)) + random.choice(get_args(uno.Symbol))

def shield_players(server: uno.UnoServer) -> uno.UnoServer:
    for p in server.players:
        if len(p.hand) == 1:
            p.is_shielded = True
    return server

def shield_all_others(server: uno.UnoServer) -> uno.UnoServer:
    "Shields all player but the active player."
    for p in server.players:
        if p != server.next_player and len(p.hand) == 1:
            p.is_shielded = True
    return server

def random_card_in_hand(server: uno.UnoServer) -> str:
    return random.randint(0,len(server.next_player.hand)-1)

def playable(c: uno.Card, tc: uno.Card, next_color: uno.Color) -> bool:
    return uno.is_wild(c) or c[0] == tc[0] or c[1] == tc[1] or c[0] == next_color

# for each of these scenarios, generate a random game state
# and then apply custom requirements.

def draw_needed_forced() -> dict:
    server = random_game_state()
    server = shield_players(server)

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
    server = random_game_state()
    server = shield_players(server)

    # look at top card. make sure nothing in your hand is playable.
    top_card = server.deck.top_card_on_discard_pile()

    if uno.is_wild(top_card):
        server.next_color = random.choice(get_args(uno.Color))

    server.next_player.hand = list(filter(
        lambda c: not playable(c, top_card, server.next_color),
        server.next_player.hand
    ))

    # what if all cards in hand were playable?
    # generate a random cards until one is not playable. add to hand.
    if not server.next_player.hand:
        random_card = random_card_no_wild()
        while playable(random_card, top_card, server.next_color):
            random_card = random_card_no_wild()

        server.next_player.hand[0] = random_card

    return {
        "input": ''.join(create_input(server, server.next_player)),
        "output": {"action": "Draw card"}
    }

def draw_unneeded() -> list[dict]:
    "Create a situation where there is a valid move but you draw anyway. TODO this might pollute train set..."
    server = random_game_state()
    server = shield_players(server)

    # look at top card. make sure there is a card in your hand that is playable.
    top_card = server.deck.top_card_on_discard_pile()

    if uno.is_wild(top_card):
        server.next_color = random.choice(get_args(uno.Color))

    random_card_i = random_card_in_hand(server)
    while not playable(server.next_player.hand[random_card_i], server.deck.top_card_on_discard_pile(), server.next_color):
        server.next_player.hand[random_card_i] = random_card_no_wild()

    server.next_player.hand = list(filter(
        lambda c: not playable(c, top_card, server.next_color),
        server.next_player.hand
    ))

    # what if all cards in hand were playable?
    # generate a random cards until one is not playable. add to hand.
    if not server.next_player.hand:
        random_card = random_card_no_wild()
        while playable(random_card, top_card, server.next_color):
            random_card = random_card_no_wild()

        server.next_player.hand[0] = random_card

    return {
        "input": ''.join(create_input(server, server.next_player)),
        "output": {"action": "Draw card"}
    }

def play_regular_symbol() -> list[dict]:
    server = random_game_state()
    server = shield_players(server)

    # make sure top card on discard is not wild.
    top_card = server.deck.top_card_on_discard_pile()
    while top_card[0] == "W":
        server.deck.play(server.deck.draw())
        top_card = server.deck.top_card_on_discard_pile()

    # create a random card in hand to match symbol of top card.
    c = random.choice(get_args(uno.Color))
    random_card_i = random_card_in_hand(server)
    random_card = c + top_card[1]
    server.next_player.hand[random_card_i] = random_card

    return {
        "input": ''.join(create_input(server, server.next_player)),
        "output": {"action": "Play card", "card": random_card}
    }

def play_regular_color() -> list[dict]:
    server = random_game_state()
    server = shield_players(server)

    # make sure top card on discard is not wild.
    top_card = server.deck.top_card_on_discard_pile()
    while top_card[0] == "W":
        server.deck.play(server.deck.draw())
        top_card = server.deck.top_card_on_discard_pile()

    # create a random card in hand to match color of top card.
    s = random.choice(get_args(uno.Symbol))
    random_card_i = random_card_in_hand(server)
    random_card = top_card[0] + s
    server.next_player.hand[random_card_i] = random_card

    return {
        "input": ''.join(create_input(server, server.next_player)),
        "output": {"action": "Play card", "card": random_card}
    }

def play_wild() -> list[dict]:
    server = random_game_state()
    server = shield_players(server)

    # this function applies if wild is on top so leave top_card alone.

    # Force random card in hand to be a wild card
    random_wild = random.choice(["WW", "WF"])
    random_card_i = random_card_in_hand(server)
    server.next_player.hand[random_card_i] = random_wild

    # choose a color in hand
    colors_in_hand = set(map(lambda c: c[0], server.next_player.hand)) - {'W'}
    # what if they only had wild cards in hand? choose a random color
    if not colors_in_hand:
        c = random.choice(get_args(uno.Color))
    else:
        c = random.choice(list(colors_in_hand))

    return {
        "input": ''.join(create_input(server, server.next_player)),
        "output": {"action": "Play card", "card": random_wild, "nextColor": c}
    }

def uno_defense() -> list[dict]:
    server = random_game_state()
    server = shield_players(server)

    # all OTHER players must be shielded.
    server = shield_all_others(server)

    # force current player to have only one card.
    current_p = server.next_player
    while len(current_p.hand) > 1:
        server.deck.play(current_p.hand.pop())

    return {
        "input": ''.join(create_input(server, server.next_player)),
        "output": {"action": "Yell UNO"}
    }

def uno_offense() -> list[dict]:
    server = random_game_state()
    server = shield_players(server)

    # force a different player to have only one card.
    random_player_i = 0
    while server.players[random_player_i] != server.next_player:
        random_player_i = random.randint(0,len(server.players)-1)

    target_p = server.players[random_player_i]
    while len(target_p.hand) > 1:
        server.deck.play(target_p.hand.pop())

    # all players but them must have shields
    for p in server.players:
        if p == target_p:
            continue
        if len(p.hand) == 1:
            p.is_shielded = True

    return {
        "input": ''.join(create_input(server, server.next_player)),
        "output": {"action": "Yell UNO"}
    }

def random_game_state() -> uno.UnoServer:
    # generate a random number of players
    n_players = random.randint(2,6)
    # agents are only used to generate relevant prompts
    s = "Do what you need to do to win"
    agents = [uno.LLMAgent(strategy=s) for _ in range(n_players)]
    server = uno.UnoServer(agents, blank_slate=True, log_level=logging.ERROR)
    random_player_i = random.randint(0,len(server.players)-1)
    server.next_player = server.players[random_player_i]

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
    generate_training_data(2000, 'autoset2k_v1')
