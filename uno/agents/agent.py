"""This class represents each agent which will be playing multiple games of uno.
All agent-specific material is tracked here but game-specific information is tracked
in Player object.
"""

class Agent:
    "MetaType for all agents."
    def act(self, prompt_dict: dict, is_turn: bool) -> dict:
        raise NotImplementedError
