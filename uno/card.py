"""This class allows for some syntactic sugar.
"""

from typing import Literal

Card = Literal[
    # Red
    "R0",
    "R1","R1","R2","R2","R3","R3","R4","R4","R5","R5","R6","R6","R7","R7","R8","R8","R9","R9",
    "RS","RS","RV","RV","RD","RD",

    # Yellow
    "Y0",
    "Y1","Y1","Y2","Y2","Y3","Y3","Y4","Y4","Y5","Y5","Y6","Y6","Y7","Y7","Y8","Y8","Y9","Y9",
    "YS","YS","YV","YV","YD","YD",

    # Green
    "G0",
    "G1","G1","G2","G2","G3","G3","G4","G4","G5","G5","G6","G6","G7","G7","G8","G8","G9","G9",
    "GS","GS","GV","GV","GD","GD",

    # Blue
    "B0",
    "B1","B1","B2","B2","B3","B3","B4","B4","B5","B5","B6","B6","B7","B7","B8","B8","B9","B9",
    "BS","BS","BV","BV","BD","BD",

    # Wilds
    "WW","WW","WW","WW",   # Wild
    "WF","WF","WF","WF"    # Wild Draw Four
]

def color(c: Card) -> str:
    return c[0]

def value(c: Card) -> str:
    return c[1]

def is_wild(c: Card) -> bool:
    return c[0] == "W"
