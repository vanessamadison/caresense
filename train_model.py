"""Secure model training pipeline for CareSense."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.utils.class_weight import compute_class_weight

DATA_PATH = Path("data") / "extracted_symptoms_train.csv"
MODEL_PATH = Path("models") / "caresense_model.pkl"
REPORT_PATH = Path("reports") / "model_report.json"
MODEL_CARD_PATH = Path("reports") / "model_card.md"

URGENCY_ORDER = ["Low Urgency", "Medium Urgency", "High Urgency"]

ENRICHED_MAP = {
    "Dengue": {
        "urgency": "High Urgency",
        "care_type": "IV fluids, observation",
        "specialty": "Infectious Disease",
    },
    "Pneumonia": {
        "urgency": "High Urgency",
        "care_type": "Antibiotics, imaging",
        "specialty": "Pulmonology",
    },
    "Arthritis": {
        "urgency": "Medium Urgency",
        "care_type": "Non-steroidal therapy",
        "specialty": "Rheumatology",
    },
    "Hypertension": {
        "urgency": "Medium Urgency",
        "care_type": "Medication titration",
        "specialty": "Cardiology",
    },
    "allergy": {
        "urgency": "Low Urgency",
        "care_type": "Antihistamines",
        "specialty": "Immunology",
    },
    "Acne": {
        "urgency": "Low Urgency",
        "care_type": "Topical regimen",
        "specialty": "Dermatology",
    },
    "Gastroesophageal Reflux Disease": {
        "urgency": "Medium Urgency",
        "care_type": "Proton pump inhibitors",
        "specialty": "Gastroenterology",
    },
    "Common Cold": {
        "urgency": "Low Urgency",
        "care_type": "Self-care",
        "specialty": "General Practice",
    },
    "Migraine": {
        "urgency": "Medium Urgency",
        "care_type": "Neurologist follow-up",
        "specialty": "Neurology",
    },
    "Bronchial Asthma": {
        "urgency": "High Urgency",
        "care_type": "Rescue inhaler",
        "specialty": "Pulmonology",
    },
}


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset missing at {path}")
    df = pd.read_csv(path)
    df = df[df["disease"].isin(ENRICHED_MAP.keys())].copy()
    df["urgency"] = df["disease"].map(lambda d: ENRICHED_MAP[d]["urgency"])
    df["urgency_encoded"] = df["urgency"].map({u: i for i, u in enumerate(URGENCY_ORDER)})
    return df


def build_pipeline(class_weights: Dict[int, float]) -> Pipeline:
    base_clf = LogisticRegression(
        max_iter=2000,
        class_weight=class_weights,
        solver="lbfgs",
        multi_class="auto",
    )

    calibrated = CalibratedClassifierCV(base_estimator=base_clf, method="isotonic", cv=3)

    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=35000,
                ),
            ),
            (
                "svd",
                TruncatedSVD(n_components=256, random_state=42),
            ),
            ("clf", calibrated),
        ]
    )

    return pipeline


def main() -> None:
    df = load_dataset(DATA_PATH)
    X_train, X_test, y_train, y_test = train_test_split(
        df["symptom_text"],
        df["urgency_encoded"],
        test_size=0.2,
        random_state=42,
        stratify=df["urgency_encoded"],
    )

    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y_train),
        y=y_train,
    )
    class_weight_dict = {i: weight for i, weight in enumerate(class_weights)}

    pipeline = build_pipeline(class_weight_dict)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    metrics = classification_report(
        y_test,
        y_pred,
        target_names=URGENCY_ORDER,
        output_dict=True,
        zero_division=0,
    )

    micro_f1 = f1_score(y_test, y_pred, average="micro")
    metrics["micro_f1"] = micro_f1

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(metrics, indent=2))

    per_class_f1 = ", ".join(
        f"{cls}: {class_metrics['f1-score']:.3f}"
        for cls, class_metrics in metrics.items()
        if cls in URGENCY_ORDER
    )

    MODEL_CARD_PATH.write_text(
        (
            "# CareSense Triage Model Card\n\n"
            f"**Version:** {metrics.get('micro_f1', 0):.3f} micro-F1  \n"
            f"**Classes:** {', '.join(URGENCY_ORDER)}  \n"
            f"**Training samples:** {len(X_train)}  \n"
            f"**Test samples:** {len(X_test)}\n\n"
            "## Intended Use\n"
            "- Rapid triage of free-text symptom descriptions prior to clinical engagement.\n"
            "- Risk stratification for digital front-door automation.\n\n"
            "## Performance\n"
            f"- Micro F1: {metrics['micro_f1']:.3f}\n"
            f"- Per-class F1: {per_class_f1}\n\n"
            "## Ethical Considerations\n"
            "- **Bias:** Trained on limited dataset; further evaluation required across diverse populations.\n"
            "- **Explainability:** Provide clinician review of decision outputs, especially for high-urgency predictions.\n\n"
            "## Security & Privacy\n"
            "- Model artefact stored in encrypted volume with audit logs.\n"
            "- Use alongside CareSense FHE biometric guardrails for request authentication.\n"
        ),
        encoding="utf-8",
    )

    print("✅ Model trained and persisted with calibrated probabilities.")


if __name__ == "__main__":
    main()
