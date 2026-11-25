from __future__ import annotations

import random
from dataclasses import dataclass

# Building blocks for a story concept. Each entry must be something an LLM critic
# can judge reliably from the text alone -- avoid counting rules ("exactly five
# words"), which models judge badly and which stop the story loop converging.

PROTAGONISTS = [
    "a lighthouse keeper who has never left the island",
    "a retired chess champion",
    "a stray dog in a busy city",
    "an AI that runs a small bakery",
    "a cartographer mapping a coastline that keeps changing",
    "a night-shift nurse",
    "a child who collects lost keys",
    "a beekeeper whose hives have gone silent",
]

CONFLICTS = [
    "a storm cuts them off from everyone they rely on",
    "an old rival returns with a claim on what they love",
    "they discover a secret someone close to them has kept",
    "they must choose between two people who both need them",
    "something precious to them goes missing",
    "a promise they made years ago comes due",
]

RESOLUTIONS = [
    "through an unlikely friendship",
    "by giving up something they value",
    "through a small act of courage",
    "by accepting what cannot be changed",
    "with a reversal the reader does not see coming",
]

CONSTRAINTS = [
    "contains no dialogue",
    "takes place within a single day",
    "is told in the second person",
    "names only one character",
    "mentions the weather in its final sentence",
]

TONES = ["wry", "melancholy", "hopeful", "eerie", "warm"]

# Per-run input. A concept is compiled once and run several times; the setting
# is what varies between those runs.
SETTINGS = [
    "a night train crossing a border",
    "a flooded library",
    "a market at dawn",
    "a hospital corridor at 3 a.m.",
    "a village the day after a festival",
    "an orbiting research station",
    "a ferry stuck in fog",
    "an empty stadium after the final match",
]


@dataclass(frozen=True)
class StoryConcept:
    protagonist: str
    conflict: str
    resolution: str
    constraint: str
    tone: str

    def rubric(self) -> str:
        """The requirements the critic judges a draft against."""
        return (
            f"- The protagonist is {self.protagonist}.\n"
            f"- The protagonist faces this conflict: {self.conflict}.\n"
            f"- The conflict is resolved {self.resolution}.\n"
            f"- The story {self.constraint}.\n"
            f"- The tone is {self.tone}."
        )

    def summary(self) -> str:
        return f"{self.protagonist} | {self.tone} | {self.constraint}"


def invent_concept(rng: random.Random) -> StoryConcept:
    return StoryConcept(
        protagonist=rng.choice(PROTAGONISTS),
        conflict=rng.choice(CONFLICTS),
        resolution=rng.choice(RESOLUTIONS),
        constraint=rng.choice(CONSTRAINTS),
        tone=rng.choice(TONES),
    )


def pick_setting(rng: random.Random) -> str:
    return rng.choice(SETTINGS)
