import csv

from regicide.collect import collect_game, main
from regicide.features import FEATURE_NAMES


def test_each_row_has_a_full_feature_vector_and_the_game_label():
    rows = collect_game("greedy", 3)
    assert rows
    assert all(len(row.features) == len(FEATURE_NAMES) for row in rows)
    assert len({(row.won, row.enemies_defeated) for row in rows}) == 1
    assert [row.decision for row in rows] == list(range(len(rows)))


def test_collection_is_deterministic_for_a_seed():
    assert collect_game("greedy", 4) == collect_game("greedy", 4)


def test_main_writes_a_csv_with_header_and_rows(tmp_path):
    out = tmp_path / "rows.csv"
    main(["--policy", "greedy", "--games", "2", "--out", str(out)])
    with open(out, newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        body = list(reader)
    assert header == ["seed", "decision", "won", "enemies_defeated", *FEATURE_NAMES]
    assert len(body) == sum(len(collect_game("greedy", seed)) for seed in (1, 2))
