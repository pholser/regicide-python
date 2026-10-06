"""A linear value model over features.extract(), stored as JSON so the game needs no numpy."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from regicide.features import FEATURE_NAMES

DEFAULT_PATH = Path(__file__).with_name("value_weights.json")


@dataclass(frozen=True)
class LinearValueModel:
    intercept: float
    coefficients: tuple[float, ...]

    def predict(self, features: Sequence[float]) -> float:
        return self.intercept + sum(w * x for w, x in zip(self.coefficients, features, strict=True))

    def save(self, path: Path = DEFAULT_PATH) -> None:
        payload = {
            "features": list(FEATURE_NAMES),
            "intercept": self.intercept,
            "coefficients": list(self.coefficients),
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> LinearValueModel:
        payload = json.loads(path.read_text())
        if tuple(payload["features"]) != FEATURE_NAMES:
            raise ValueError(f"{path} was fitted on a different feature set")
        return cls(payload["intercept"], tuple(payload["coefficients"]))
