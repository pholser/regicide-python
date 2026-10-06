"""Fit a linear value model to collected rows, predicting enemies defeated.

Run with: python -m regicide.fit_value FILE.csv [--holdout-fraction F]

Needs numpy (the optional "train" extra). Splits by seed so that rows from one
game never appear on both sides of the split.
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from regicide.features import FEATURE_NAMES

LABEL = "enemies_defeated"


@dataclass(frozen=True)
class Dataset:
    seeds: np.ndarray
    features: np.ndarray
    labels: np.ndarray


def load(path: str) -> Dataset:
    with open(path, newline="") as handle:
        rows = list(csv.DictReader(handle))
    seeds = np.array([int(row["seed"]) for row in rows])
    features = np.array([[float(row[name]) for name in FEATURE_NAMES] for row in rows])
    labels = np.array([float(row[LABEL]) for row in rows])
    return Dataset(seeds, features, labels)


def split_by_seed(data: Dataset, holdout_fraction: float) -> tuple[Dataset, Dataset]:
    unique = np.unique(data.seeds)
    cutoff = unique[int(len(unique) * (1 - holdout_fraction))]
    train = data.seeds < cutoff
    return (
        Dataset(data.seeds[train], data.features[train], data.labels[train]),
        Dataset(data.seeds[~train], data.features[~train], data.labels[~train]),
    )


def fit(features: np.ndarray, labels: np.ndarray) -> np.ndarray:
    design = np.hstack([np.ones((len(features), 1)), features])
    weights, *_ = np.linalg.lstsq(design, labels, rcond=None)
    return weights


def predict(weights: np.ndarray, features: np.ndarray) -> np.ndarray:
    return np.hstack([np.ones((len(features), 1)), features]) @ weights


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fit a linear value model.")
    parser.add_argument("path")
    parser.add_argument("--holdout-fraction", type=float, default=0.25)
    args = parser.parse_args(argv)

    data = load(args.path)
    train, test = split_by_seed(data, args.holdout_fraction)
    weights = fit(train.features, train.labels)

    model_error = predict(weights, test.features) - test.labels
    baseline_error = train.labels.mean() - test.labels
    print(f"train rows {len(train.labels)}, held-out rows {len(test.labels)}")
    print(f"held-out MAE: model {np.abs(model_error).mean():.3f}, "
          f"predict-the-mean {np.abs(baseline_error).mean():.3f}")
    print(f"held-out RMSE: model {np.sqrt((model_error**2).mean()):.3f}, "
          f"predict-the-mean {np.sqrt((baseline_error**2).mean()):.3f}")
    print("coefficients:")
    print(f"  intercept: {weights[0]:+.3f}")
    for name, weight in zip(FEATURE_NAMES, weights[1:]):
        print(f"  {name}: {weight:+.3f}")


if __name__ == "__main__":
    main()
