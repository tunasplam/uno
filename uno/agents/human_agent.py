import json
import sys
import questionary
from .agent import Agent
from ..card import is_wild
from ..utils import _get_resource

class HumanAgent(Agent):
    "For when humans want to play the game."
    def __init__(self, name: str):
        self.name = name

    def act(self, prompt_dict: dict, is_turn: bool) -> str:
        # give humans agents the context but they do not need anything else
        shell = HumanShell(prompt_dict['context'], is_turn)
        while not shell.action_complete:
            shell.prompt()
        return shell.return_value

class HumanShell:
    "Simple command line interface whereby humans can play the game."

    def __init__(self, context: str, is_turn: bool):
        self.intro = "Welcome to uno. Type help or ? to list commands.\n"
        self.return_value: str = None
        self.context: str = context
        self.action_complete = False
        self.is_turn = is_turn

    def prompt(self) -> str | None:
        response = questionary.form(
            first = questionary.select("Select an action to take", choices=self.build_prompt())
        ).ask()

        match response['first']:
            # each of these functions needs to return to valid json string
            # they return True to close the command loop since they finish the turn.
            case "Do nothing":
                self.return_value = '{"action": "Do nothing"}'
                self.action_complete = True
            case "Yell UNO":
                self.return_value = '{"action": "Yell UNO"}'
                self.action_complete = True
            case "Draw card":
                self.return_value = '{"action": "Draw card"}'
                self.action_complete = True
            case "Play card":
                card = input("What card do you want to play\n> ")
                r = {"action": "Play card", "card": card}
                if is_wild(card):
                    next_color = input("You played a wild card. What color would you like next?\n> ")
                    r |= {"nextColor": next_color}
                self.return_value = json.dumps(r)
                print(self.return_value)
                self.action_complete = True

            # these actions do not end the current turn.
            case "Show context":
                print(self.context)
            case "Show rules":
                print(_get_resource('uno.resources', 'uno_rules.txt'))
            case "Show instructions":
                print(_get_resource('uno.resources', 'instructions.txt'))
            case "Quit game":
                sys.exit()

    def build_prompt(self) -> list[str]:
        choices = [
            "Do nothing",
            "Yell UNO",
            "Show context",
            "Show rules",
            "Show instructions",
            "Quit game"
        ]

        if self.is_turn:
            choices = ["Draw card", "Play card"] + choices

        return choices
