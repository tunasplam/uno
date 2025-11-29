"""This class is used by the uno server to represent each player playing the game.
All game-specific information pertaining to each player is stored here.
"""

from collections import deque
from importlib.resources import files
import json
import logging
from typing import Literal

from .agent import Agent
from .card import Card, color

class Player:

    def __init__(self, pid: int, request_queue: deque[dir], agent: Agent):

        # When a player is created, they are given a shuffled hand.
        self.hand: list[str] = []
        self.id = pid
        # the model driving this player.
        self.agent = agent

        # each player is directed where to send their requests.
        self.request_queue = request_queue

        # if one is shielded then they do not have to draw cards if
        # someone yells uno while they have one card.
        self.is_shielded = False

        # for logging game results.
        self.result: Literal["Winner", "Loser"] = None

        # messages that will be given to the AI as context.
        self.message_queue: list[str] = []

    def give(self, card: str):
        self.hand.append(card)

    def message(self, msg: str):
        self.message_queue.append(msg)

    def clear_messages(self):
        self.message_queue.clear()

    def send_context_and_prompt(self, context: str):
        "Gives a player the world state. This prompts the agent's request, if any."
        logging.info("Prompting")
        prompt = {
            "rules": _get_resource('uno.resources', 'uno_rules.txt'),
            "context": context,
            "instructions": _get_resource('uno.resources', 'instructions.txt'),
            "strategy": self.agent.strategy
        }

        raw_response: str = self.agent.act(prompt)
        try:
            response = json.loads(raw_response)
        except json.JSONDecodeError as e:
            self.message("Invalid response. Send JSON.")
            return

        self.take_action(response)

    def take_action(self, action: dict):
        match action["action"]:
            case "Do nothing":
                return

            case "Play card":
                # NOTE we do not need to validate card. if its a bad card, its not in their hand
                # and that will trigger the error.
                c: Card = action["card"]

                if c not in self.hand:
                    self.message(f"You do not have card {c} in your hand.")
                    return

                if color(c) == "W":
                    if not action["nextColor"]:
                        self.message(f"You played a wild (W) card {c} so must indicate the next color.")
                        return
                    if action["nextColor"] not in ("Y", "G", "R", "B"):
                        self.message(f"Invalid color {action["nextColor"]}")
                        return

                if color(c) != "W" and "nextColor" in action:
                    self.message(f"You played non-wild card {c} but tried to change the color.")
                    return

                self.hand.remove(c)

        # if the request is invalid then server will send a message to the player's queue.
        self.request_queue.append(action | {"playerID": self.id,})

def _get_resource(module: str, name: str) -> str:
    """Loads a resource from the package.

    call like this:
        resource_text = _get_resource('epiphany_python_tools.Library_Maps.resources.[folder]', '[filename]')

    see second response:
    https://stackoverflow.com/questions/1395593/managing-resources-in-a-python-project

    Args:
        module (str): path to resource (using python module format)
        name (str): name of resource being loaded

    Returns:
        str: text contents of the resource
    """
    return files(module).joinpath(name).read_text(encoding='utf-8')
