import logging
from random import shuffle

from .card import Card

STANDARD_DECK = [
    # Red
    "R0",
    "R1","R1","R2","R2","R3","R3","R4","R4","R5","R5","R6","R6","R7","R7","R8","R8","R9","R9",
    "RS","RS","RR","RR","RD","RD",

    # Yellow
    "Y0",
    "Y1","Y1","Y2","Y2","Y3","Y3","Y4","Y4","Y5","Y5","Y6","Y6","Y7","Y7","Y8","Y8","Y9","Y9",
    "YS","YS","YR","YR","YD","YD",

    # Green
    "G0",
    "G1","G1","G2","G2","G3","G3","G4","G4","G5","G5","G6","G6","G7","G7","G8","G8","G9","G9",
    "GS","GS","GR","GR","GD","GD",

    # Blue
    "B0",
    "B1","B1","B2","B2","B3","B3","B4","B4","B5","B5","B6","B6","B7","B7","B8","B8","B9","B9",
    "BS","BS","BR","BR","BD","BD",

    # Wilds
    "WW","WW","WW","WW",   # Wild
    "WF","WF","WF","WF"    # Wild Draw Four
]

class Deck:

    def __init__(self, forced_top_card: Card | None):
        self.cards = STANDARD_DECK.copy()
        shuffle(self.cards)

        # these are the cards on the discard pile. never needs interaction
        # except when interacting with the deck.
        if forced_top_card:
            self.discard_pile: list[Card] = [forced_top_card]
        else:
            self.discard_pile: list[Card] = [self.draw()]

    def draw(self) -> Card:
        if not self.cards:
            logging.info("...the discard pile reshuffled...")
            shuffle(self.discard_pile)
            # empty the discard pile onto the new deck
            self.cards = self.discard_pile.copy()
            self.discard_pile = []

        return self.cards.pop()

    def play(self, c: Card):
        self.discard_pile.append(c)

    def top_card_on_discard_pile(self):
        return self.discard_pile[-1]
