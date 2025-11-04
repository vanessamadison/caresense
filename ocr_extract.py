"""Dataset ingestion utility with OCR + integrity checks."""

from __future__ import annotations

import csv
import hashlib
from argparse import ArgumentParser
from pathlib import Path
from typing import Iterable

import pandas as pd
from PIL import Image
import pytesseract

DEFAULT_IMAGE_DIR = Path("data") / "Symptom2Disease_dataset_train"
DEFAULT_LABELS = Path("data") / "Symptom2Disease_dataset_train.csv"
DEFAULT_OUTPUT = Path("data") / "extracted_symptoms_train.csv"


def extract_symptom_text(image_path: Path, lang: str = "eng") -> str:
    """Perform OCR on the provided image, returning cleaned symptom text."""
    image = Image.open(image_path)
    raw_text = pytesseract.image_to_string(image, lang=lang)
    if "Symptoms:" in raw_text:
        return raw_text.split("Symptoms:")[-1].strip()
    return raw_text.strip()


def iter_labelled_images(image_dir: Path, labels: pd.DataFrame) -> Iterable[tuple[Path, str]]:
    label_map = dict(zip(labels["file_name"], labels["disease"]))
    for path in image_dir.glob("*"):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        key = f"{image_dir.name}/{path.name}"
        disease = label_map.get(key)
        if disease:
            yield path, disease


def main(
    image_dir: Path = DEFAULT_IMAGE_DIR,
    label_csv: Path = DEFAULT_LABELS,
    output_csv: Path = DEFAULT_OUTPUT,
    lang: str = "eng",
) -> None:
    labels_df = pd.read_csv(label_csv, header=None, names=["file_name", "disease"])

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    records = []

    for path, disease in iter_labelled_images(image_dir, labels_df):
        try:
            text = extract_symptom_text(path, lang=lang)
            if not text:
                continue
            record_id = hashlib.sha256(f"{path.name}:{disease}".encode("utf-8")).hexdigest()
            records.append(
                {
                    "record_id": record_id,
                    "symptom_text": text,
                    "disease": disease,
                }
            )
        except Exception as exc:  # pragma: no cover - logging side effect
            print(f"[WARN] Failed OCR for {path}: {exc}")

    if not records:
        raise RuntimeError("No OCR records produced; verify dataset paths.")

    with output_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["record_id", "symptom_text", "disease"])
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ Extracted {len(records)} labelled samples -> {output_csv}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Extract symptom text from labelled medical reports.")
    parser.add_argument("--image-dir", type=Path, default=DEFAULT_IMAGE_DIR)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--lang", type=str, default="eng", help="Tesseract language pack (e.g. eng, spa).")
    args = parser.parse_args()
    main(args.image_dir, args.labels, args.output, args.lang)
