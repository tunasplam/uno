"""
This is the object which tracks the game. The main game loop is run here.
Keeps track of world state. Has a FIFO queue which accepts requests
from player agents in the order which they need to be processed in.

Requests:

{
    "playerID": int,
    "action": ["Do nothing", "Play card", "Draw card", "Yell UNO"],
    "card": Card
}

Returns:
[
    Card | You Won! | Error
]

Error : {
    Not your turn | Invalid Card | Must draw Card
}

TODO list:

- there is currently inconsistency surrounding forced draws. Calling uno
gives UNO_PENALTY cards to person caught whereas playing a draw card
requires them to actually perform draw actions.

- refactor deck cards -> draw_pile

- override uno_rules.txt and instructions.txt with user supplied files

- tui for actually playing uno against the agents
    - this will mean there will likely be a player agent. send_context_and_prompt
    calls self.agent.act(prompt) which, for HumanAgent, should format the prompt nicely as
    a tui and the tui interaction will return the response.
    - will be likely impossible to win bc the AI will be too fast for calling uno. give
    them time lags if a human is playing?

"""

from collections import deque
import logging
import sys
import time
import typing

from .agents import Agent
from .card import Card, is_wild, color, value
from .deck import Deck
from .player import Player

Color = typing.Literal["Y", "G", "B", "R"]

class UnoServer:
    def __init__(
        self, players: list[Agent], player_starting_hand: int = 7,
        uno_penalty=7, forced_top_card: Card=None, blank_slate: bool=False,
        log_level: int=logging.INFO
    ):
        """Manages a game of Uno.

        Args:
            players (list[Agent]): The agents requesting to be used in the game.
                Order of this list specifies starting order.
            player_starting_hand (int, optional): How many cards to deal to players
                at game start. Defaults to 7.
            uno_penalty (int, optional): How many cards a player needs to draw if they
                caught with one card while unshielded. Defaults to 7.
            forced_top_card (Card, optional): Forces top card to be a given card.
                Does not actually remove it from draw deck or any player's hands so
                this likely introduces a duplicate. Defaults to None.
            blank_slate (bool, optional): Does not hand cards to players or reveal top card.
                Good for mock scenarios like generating random train datasets.
        """

        # allow logging to stdout
        root = logging.getLogger()
        root.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        root.addHandler(handler)

        self.deck = Deck(forced_top_card)
        self.uno_penalty = uno_penalty

        # requests will be dict payloads.
        self.request_queue: deque[dict] = deque([])

        # which color to request next
        self.next_color: Color = None

        # spawn the players. their index in this list is turn order.
        # the person who is at the top of this list is the person
        # whose turn it is.
        # For now, randomly assign the starting order.
        self.players: deque[Player] = deque([
            Player(n+1, self.request_queue, agent) for n, agent in enumerate(players)
        ])
        self.next_player = self.players[0]

        # keeps track of how many cards the current player must draw.
        self.must_draw_count = 0

        if blank_slate:
            return

        # deal the cards.
        for _ in range(player_starting_hand):
            for p in self.players:
                p.give(self.deck.draw())

        # resolve the top card on the deck
        self.resolve(
            self.deck.top_card_on_discard_pile(),
            next_color=color(self.deck.top_card_on_discard_pile())
        )
        # resolving would have iterated next player at least once so undo.
        p = self.players.pop()
        self.players.insert(0, p)
        self.next_player = p

        # keeps track if the game is officially playing.
        self.playing = True

    def play_game(self):
        while self.playing:
            for p in self.players:
                self.broadcast_world_state(p)

            while self.request_queue:
                self.process_request(self.request_queue.popleft())

            # :)
            time.sleep(.2)

    def broadcast_world_state(self, p: Player):
        "Provides context to our players"
        is_turn = p == self.next_player
        context = self.build_context(p, is_turn)
        p.send_context_and_prompt(context, is_turn)

    def build_context(self, p: Player, is_turn: bool) -> list[str]:
        context= []

        # personal stats
        context.append("Cards")
        context.append(" ".join(p.hand))

        # stats on players
        context.append("Player | Cards | shielded:")
        for p2 in self.players:
            context.append(f"{p2.id} {len(p2.hand)} {"T" if p2.is_shielded else "F"}")

        # stats on deck
        context.append(f"{len(self.deck.cards)} card(s) in draw deck.")
        context.append(f"Top card: {self.deck.top_card_on_discard_pile()}")

        if is_turn and self.must_draw_count > 0:
            p.message(f"You must draw {self.must_draw_count} card(s)")

        if is_wild(self.deck.top_card_on_discard_pile()):
            p.message(f"Chosen color: {self.next_color}")

        context.append("Messages:")
        context.append(_format_messages(p.message_queue))
        p.clear_messages()
        logging.info("\n".join(context))
        return context

    def process_request(self, r: dict):
        """
        {
        "playerID": int,
        "action": ["Do nothing", "Play card", "Draw card", "Yell UNO"],
        "card": Card,
        "nextColor: ["Y","R","B","G","W"]
        }
        """
        p = self.get_player(r["playerID"])
        match r["action"]:
            case "Play card":
                if "nextColor" in r:
                    self.play_card(p, r["card"], r["nextColor"])
                else:
                    self.play_card(p, r["card"])

            case "Draw card":
                self.draw(p)

            case "Yell UNO":
                self.yell_uno(p)

            case _:
                p.message("Invalid request.")

    def yell_uno(self, p: Player):
        logging.info("Player %s yelled UNO...", p)

        # if a person is yelling uno when they have one card,
        # they are putting a shield upon them.
        if len(p.hand) == 1:
            logging.info("...they are shielded!")
            p.message("You are shielded.")
            p.is_shielded = True
            return

        # when a person is yelling uno and another person has one card,
        # that person must draw 7 cards.
        for p2 in self.players:
            if p != p2 and \
                len(p2.hand) == 1 and \
                not p2.is_shielded:

                logging.info("THEY CAUGHT SOMEBODY!")
                logging.info("Giving %s cards to Player %s", self.uno_penalty, p2.id)
                p.message("You caught somebody!")
                p2.message("Somebody said uno before you.")
                for _ in range(self.uno_penalty):
                    p2.give(self.deck.draw())
                return

        logging.info("...nothing happened.")

    def draw(self, p: Player):
        logging.info("Player %s tried to draw a card...", p.id)

        if p != self.next_player:
            logging.info("...it wasn't their turn!")
            p.message("Not your turn.")
            return

        if not self.deck:
            logging.info("...the draw deck is empty!")
            p.message("No more cards to draw!")
            return

        # decrement draw count, if necessary
        self.must_draw_count = max(0,self.must_draw_count-1)
        logging.info("...they drew a card.")
        p.give(self.deck.draw())

    def iterate_next_player(self):
        # pop from the player queue and push to the back
        self.players.append(self.players.popleft())
        self.next_player = self.players[0]
        logging.info("It is player %s turn.", self.next_player.id)

    def play_card(self, p: Player, c: Card, next_color: str|None=None):
        logging.info("Player %s tried to play %s...", p.id, c)
        if p != self.next_player:
            logging.info("...it wasn't their turn!")
            p.message("It is not your turn.")
            p.give(c)
            return

        if not self.valid(c):
            logging.info("...it wasn't a valid card!")
            p.message("Invalid card.")
            p.give(c)
            return

        if self.must_draw_count > 0:
            logging.info("...they're supposed to draw a card!")
            p.message("You must draw a card.")
            p.give(c)
            return

        # if player has one card, they win!
        if len(p.hand) == 0:
            self.declare_winner(p)
            return

        logging.info("...they played %s.", c)
        self.resolve(c, next_color)
        self.deck.play(c)

    def declare_winner(self, p: Player):
        "Declares player p the winner and all other players the loser."
        self.playing = False
        for p2 in self.players:
            if p != p2:
                p2.result = "Loser"
        logging.info("Player %s WON!", p.id)
        p.result = "Winner"

    def resolve(self, c: Card, next_color: str|None=None):
        match value(c):
            case "S":
                self.iterate_next_player()
                self.iterate_next_player()
            case "D":
                self.must_draw_count += 2
                self.iterate_next_player()
            case "F":
                self.must_draw_count += 4
                self.next_color = next_color
                self.iterate_next_player()
            case "W":
                self.next_color = next_color
                self.iterate_next_player()
            case "R":
                p = self.players.popleft()
                self.players = deque(reversed(self.players))
                self.players.append(p)
                self.next_player = self.players[0]
            case _:
                self.iterate_next_player()

        self.next_color = next_color if color(c) == "W" else color(c)

    def valid(self, c: Card) -> bool:
        return is_wild(c) or \
            color(c) == self.next_color or \
            value(c) == value(self.deck.top_card_on_discard_pile()) or \
            self.next_color == 'W' # should only happen if wild card was first card to flip.

    def get_player(self, pid: int) -> Player:
        if pid <= 0 or pid > len(self.players):
            raise RuntimeError(f"Tried to get invalid player {pid}")
        for p in self.players:
            if p.id == pid:
                return p

def _format_messages(message_queue: list[str]) -> str:
    if not message_queue:
        return ""
    return "\n".join([f"- {m}" for m in message_queue])

class Error:
    "This means that the agent did something bad. Also hands their card back."
    def __init__(self, msg: str, c: Card|None=None):
        self.msg = msg
        self.c = c
