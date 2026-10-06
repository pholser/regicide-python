from regicide.features import FEATURE_NAMES
from regicide.value_model import LinearValueModel


def test_save_and_load_round_trip(tmp_path):
    model = LinearValueModel(1.5, tuple(float(i) for i in range(len(FEATURE_NAMES))))
    path = tmp_path / "weights.json"
    model.save(path)
    assert LinearValueModel.load(path) == model


def test_predict_is_intercept_plus_dot_product():
    model = LinearValueModel(2.0, (1.0, 0.5))
    assert model.predict([3.0, 4.0]) == 2.0 + 3.0 + 2.0
