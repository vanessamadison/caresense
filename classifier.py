# classifier.py

import joblib

urgency_map = {0: "Low Urgency", 1: "Medium Urgency", 2: "High Urgency"}

# Expanded care mapping
urgency_enrichment = {
    "Low Urgency": {
        "care_type": "At-home care, hydration, rest",
        "specialty": "General Practice",
        "guideline": "Use over-the-counter remedies. Monitor symptoms for changes."
    },
    "Medium Urgency": {
        "care_type": "Primary care visit recommended",
        "specialty": "Internal Medicine",
        "guideline": "Schedule a visit if symptoms persist beyond 24–48 hours."
    },
    "High Urgency": {
        "care_type": "Immediate medical attention required",
        "specialty": "Emergency Medicine",
        "guideline": "Go to urgent care or call emergency services if symptoms worsen."
    }
}

model = joblib.load("models/caresense_model.pkl")

def classify_symptom(text):
    prediction = model.predict([text])[0]
    confidence = model.predict_proba([text])[0][prediction]

    urgency_label = urgency_map[prediction]
    enrichment = urgency_enrichment[urgency_label]

    return {
        "urgency": urgency_label,
        "confidence": confidence * 100,
        "care_type": enrichment["care_type"],
        "specialty": enrichment["specialty"],
        "guideline": enrichment["guideline"]
    }
