from pathlib import Path

import pytest

import src.image_validator as validator


def test_missing_validation_weights_are_a_controlled_error(monkeypatch, tmp_path):
    monkeypatch.setattr(validator, "MOBILENET_V2_WEIGHTS_PATH", Path(tmp_path / "missing.h5"))
    monkeypatch.setattr(validator, "MOBILENET_V2_WEIGHTS_PATH_CONFIGURED", True)
    with pytest.raises(validator.ValidationModelLoadError, match="unavailable"):
        validator.validation_weights_path()


def test_validation_weights_integrity_mismatch_is_rejected(monkeypatch, tmp_path):
    path = Path(tmp_path / "bad.h5")
    path.write_bytes(b"not trusted weights")
    monkeypatch.setattr(validator, "MOBILENET_V2_WEIGHTS_PATH", path)
    monkeypatch.setattr(validator, "MOBILENET_V2_WEIGHTS_PATH_CONFIGURED", True)
    with pytest.raises(validator.ValidationModelLoadError, match="integrity"):
        validator.validation_weights_path()


def test_missing_imagenet_labels_are_a_controlled_error(monkeypatch, tmp_path):
    monkeypatch.setattr(validator, "IMAGENET_CLASS_INDEX_PATH", Path(tmp_path / "missing.json"))
    monkeypatch.setattr(validator, "IMAGENET_CLASS_INDEX_PATH_CONFIGURED", True)
    with pytest.raises(validator.ValidationModelLoadError, match="class labels are unavailable"):
        validator.imagenet_class_index()


def test_default_validator_download_is_hash_verified(monkeypatch, tmp_path):
    requested = {}

    def fake_get_file(filename, origin, **kwargs):
        requested.update(filename=filename, origin=origin, **kwargs)
        return str(tmp_path / filename)

    monkeypatch.setattr(validator, "MOBILENET_V2_WEIGHTS_PATH", tmp_path / "missing.h5")
    monkeypatch.setattr(validator, "MOBILENET_V2_WEIGHTS_PATH_CONFIGURED", False)
    monkeypatch.setattr(validator, "get_file", fake_get_file)
    with pytest.raises(validator.ValidationModelLoadError, match="could not be obtained|integrity"):
        validator.validation_weights_path()
    assert requested["origin"] == validator.MOBILENET_V2_WEIGHTS_ORIGIN
    assert requested["file_hash"] == validator.MOBILENET_V2_WEIGHTS_SHA256
    assert requested["hash_algorithm"] == "sha256"
    assert requested["cache_dir"] == str(validator.MODEL_CACHE_DIR)
