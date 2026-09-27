"""Reproducibly train the verified EfficientNetB0 catfish multitask model.

Dataset root must contain `fingerling`, `juvenile`, and `adult` image folders
and the corresponding `{class}.xlsx` files from the research collection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.preprocessing import StandardScaler

from src.model import build_prediction_model

SEED = 42
CLASS_NAMES = ["fingerling", "juvenile", "adult"]
TARGETS = ["SL_cm", "TL_cm", "Weight_g"]


def canonical_id(class_name: str, value: object) -> str:
    return f"{class_name}_{str(value).strip().lower().replace(' ', '_')}"


def read_metadata(root: Path, class_name: str, label: int) -> pd.DataFrame:
    path = root / f"{class_name}.xlsx"
    if not path.is_file():
        raise FileNotFoundError(f"Missing metadata workbook: {path}")
    raw = pd.read_excel(path, header=None)
    if raw.shape[1] < 4:
        raise ValueError(f"{path} must contain filename, SL_cm, TL_cm, and Weight_g columns")
    frame = raw.iloc[:, :4].copy()
    frame.columns = ["Filename", *TARGETS]
    frame = frame.iloc[1:] if not pd.api.types.is_numeric_dtype(frame["SL_cm"]) else frame
    frame[TARGETS] = frame[TARGETS].apply(pd.to_numeric, errors="raise")
    frame["class_name"], frame["class_label"] = class_name, label
    frame["fish_id"] = [canonical_id(class_name, value) for value in frame["Filename"]]
    return frame


def build_index(root: Path) -> pd.DataFrame:
    metadata = pd.concat([read_metadata(root, name, i) for i, name in enumerate(CLASS_NAMES)], ignore_index=True)
    if metadata.fish_id.duplicated().any() or (metadata[TARGETS] <= 0).any().any() or not (metadata.SL_cm < metadata.TL_cm).all():
        raise ValueError("Fish metadata is duplicate, non-positive, or has SL_cm >= TL_cm.")
    records = []
    for _, row in metadata.iterrows():
        folder = root / row.class_name / str(row.Filename)
        # The verified collection stores multiple images in a fish-ID directory.
        candidates = list(folder.glob("*")) if folder.is_dir() else list((root / row.class_name).glob(f"**/{row.Filename}*"))
        images = [path for path in candidates if path.suffix.lower() in {".jpg", ".jpeg", ".png"}]
        if not images:
            raise FileNotFoundError(f"No images found for fish {row.fish_id}")
        for image in images:
            records.append({**row.to_dict(), "image_path": str(image)})
    index = pd.DataFrame(records)
    if index.empty:
        raise ValueError("No usable images found.")
    return index


def grouped_split(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    fish = frame[["fish_id", "class_label"]].drop_duplicates()
    rng = np.random.default_rng(SEED)
    assignments = {"train": [], "validation": [], "test": []}
    for _, group in fish.groupby("class_label"):
        ids = group.fish_id.to_numpy().copy(); rng.shuffle(ids)
        train_count, val_count = round(.70 * len(ids)), round(.15 * len(ids))
        assignments["train"] += ids[:train_count].tolist()
        assignments["validation"] += ids[train_count:train_count + val_count].tolist()
        assignments["test"] += ids[train_count + val_count:].tolist()
    splits = {name: frame[frame.fish_id.isin(ids)].reset_index(drop=True) for name, ids in assignments.items()}
    assert not (set(splits["train"].fish_id) & set(splits["validation"].fish_id) or set(splits["train"].fish_id) & set(splits["test"].fish_id) or set(splits["validation"].fish_id) & set(splits["test"].fish_id))
    return splits


def make_dataset(frame, targets, training=False, batch_size=16):
    paths, labels = frame.image_path.astype(str).to_numpy(), frame.class_label.astype("int32").to_numpy()
    ds = tf.data.Dataset.from_tensor_slices((paths, labels, targets.astype("float32")))
    def decode(path, label, values):
        image = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        image = tf.image.resize_with_pad(tf.cast(image, tf.float32), 224, 224)
        image.set_shape((224, 224, 3))
        return image, {"class_output": label, "sl_output": values[0], "tl_output": values[1], "weight_output": values[2]}
    ds = ds.map(decode, num_parallel_calls=tf.data.AUTOTUNE)
    if training: ds = ds.shuffle(len(frame), seed=SEED, reshuffle_each_iteration=True)
    return ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)


def scaled(frame, scalers):
    return np.column_stack([scalers["standard_length_cm"].transform(frame[["SL_cm"]])[:, 0], scalers["total_length_cm"].transform(frame[["TL_cm"]])[:, 0], scalers["weight_g_log1p"].transform(np.log1p(frame[["Weight_g"]]))[:, 0]])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts/efficientnetb0_multitask"))
    parser.add_argument("--head-epochs", type=int, default=12)
    parser.add_argument("--fine-epochs", type=int, default=10)
    args = parser.parse_args()
    random.seed(SEED); np.random.seed(SEED); tf.keras.utils.set_random_seed(SEED)
    try: tf.config.experimental.enable_op_determinism()
    except Exception: pass
    index, out = build_index(args.dataset_root), args.artifacts_dir
    out.mkdir(parents=True, exist_ok=True)
    splits = grouped_split(index)
    manifest = pd.concat([part.assign(split=name) for name, part in splits.items()], ignore_index=True)
    manifest.to_csv(out / "split_manifest.csv", index=False)
    scalers = {"standard_length_cm": StandardScaler().fit(splits["train"][["SL_cm"]]), "total_length_cm": StandardScaler().fit(splits["train"][["TL_cm"]]), "weight_g_log1p": StandardScaler().fit(np.log1p(splits["train"][["Weight_g"]]))}
    serial_scalers = {name: {"mean": float(value.mean_[0]), "scale": float(value.scale_[0])} for name, value in scalers.items()}
    (out / "class_names.json").write_text(json.dumps(CLASS_NAMES, indent=2))
    (out / "biometric_scalers.json").write_text(json.dumps(serial_scalers, indent=2))
    (out / "preprocessing.json").write_text(json.dumps({"input_size": [224, 224], "resize": "resize_with_pad", "input_range": "0..255", "backbone_preprocessing": "EfficientNetB0 internal"}, indent=2))
    train_ds, val_ds, test_ds = (make_dataset(splits[name], scaled(splits[name], scalers), name == "train") for name in ("train", "validation", "test"))
    model = build_prediction_model(augmentation=True)
    losses = {"class_output": "sparse_categorical_crossentropy", **{name: tf.keras.losses.Huber() for name in ("sl_output", "tl_output", "weight_output")}}
    weights = {"class_output": 1., "sl_output": .25, "tl_output": .25, "weight_output": .5}
    checkpoint = out / "model.keras"
    callbacks = [tf.keras.callbacks.ModelCheckpoint(checkpoint, monitor="val_loss", save_best_only=True), tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True), tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", patience=2, factor=.3)]
    model.compile(tf.keras.optimizers.Adam(3e-4), loss=losses, loss_weights=weights, metrics={"class_output": "accuracy"})
    history = model.fit(train_ds, validation_data=val_ds, epochs=args.head_epochs, callbacks=callbacks)
    backbone = model.get_layer("efficientnetb0_backbone"); backbone.trainable = True
    for layer in backbone.layers[:int(len(backbone.layers) * .75)]: layer.trainable = False
    for layer in backbone.layers:
        if isinstance(layer, tf.keras.layers.BatchNormalization): layer.trainable = False
    model.compile(tf.keras.optimizers.AdamW(1e-5, weight_decay=1e-5, clipnorm=1.), loss=losses, loss_weights=weights, metrics={"class_output": "accuracy"})
    fine = model.fit(train_ds, validation_data=val_ds, epochs=args.fine_epochs, callbacks=callbacks)
    model = tf.keras.models.load_model(checkpoint, compile=False); raw = model.predict(test_ds, verbose=0)
    predicted = raw[0].argmax(1); truth = splits["test"].class_label.to_numpy()
    _, _, f1, _ = precision_recall_fscore_support(truth, predicted, labels=[0, 1, 2], zero_division=0)
    metrics = {"image_accuracy": float(accuracy_score(truth, predicted)), "image_macro_f1": float(f1.mean()), "test_images": len(splits["test"]), "test_fish": int(splits["test"].fish_id.nunique())}
    pd.DataFrame({"fish_id": splits["test"].fish_id, "actual_label": truth, "predicted_label": predicted, **{f"prob_{name}": raw[0][:, i] for i, name in enumerate(CLASS_NAMES)}}).to_csv(out / "test_predictions.csv", index=False)
    (out / "training_history.json").write_text(json.dumps({"head": history.history, "fine_tune": fine.history}, indent=2))
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    (out / "manifest.json").write_text(json.dumps({"model_name": "EfficientNetB0", "model_version": "v1", "model_sha256": digest, "seed": SEED, "tensorflow": tf.__version__, "python": platform.python_version(), "split": "deterministic stratified fish-grouped 70/15/15 reconstruction"}, indent=2))
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__": main()
