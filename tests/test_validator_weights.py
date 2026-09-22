from pathlib import Path

import pytest

import src.image_validator as validator


def test_missing_validation_weights_are_a_controlled_error(monkeypatch, tmp_path):
    monkeypatch.setattr(validator, "MOBILENET_V2_WEIGHTS_PATH", Path(tmp_path / "missing.h5"))
    with pytest.raises(validator.ValidationModelLoadError, match="unavailable"):
        validator.validation_weights_path()


def test_validation_weights_integrity_mismatch_is_rejected(monkeypatch, tmp_path):
    path = Path(tmp_path / "bad.h5")
    path.write_bytes(b"not trusted weights")
    monkeypatch.setattr(validator, "MOBILENET_V2_WEIGHTS_PATH", path)
    with pytest.raises(validator.ValidationModelLoadError, match="integrity"):
        validator.validation_weights_path()


def test_missing_imagenet_labels_are_a_controlled_error(monkeypatch, tmp_path):
    monkeypatch.setattr(validator, "IMAGENET_CLASS_INDEX_PATH", Path(tmp_path / "missing.json"))
    with pytest.raises(validator.ValidationModelLoadError, match="class labels are unavailable"):
        validator.imagenet_class_index()
