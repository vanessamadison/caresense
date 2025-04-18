import joblib

model = joblib.load("models/caresense_model.pkl")

urgency_map = {0: "Low Urgency", 1: "Medium Urgency", 2: "High Urgency"}
urgency_enrichment = {
    "Low Urgency": {
        "care_type": "At-home care or pharmacy consultation",
        "specialty": "General Practice"
    },
    "Medium Urgency": {
        "care_type": "Schedule with a primary care provider",
        "specialty": "Internal Medicine"
    },
    "High Urgency": {
        "care_type": "Seek immediate medical attention",
        "specialty": "Emergency Medicine"
    }
}

def classify_symptom(text):
    prediction = model.predict([text])[0]
    confidence = model.predict_proba([text])[0][prediction]
    urgency_label = urgency_map[prediction]
    enrichment = urgency_enrichment[urgency_label]

    return {
        "urgency": urgency_label,
        "confidence": confidence * 100,
        "care_type": enrichment["care_type"],
        "specialty": enrichment["specialty"]
    }
