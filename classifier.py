import joblib

# Map urgency index to readable label
urgency_map = {0: "Low Urgency", 1: "Medium Urgency", 2: "High Urgency"}

# Expanded care guidance based on urgency
urgency_enrichment = {
    "Low Urgency": {
        "care_type": "Rest, hydration, over-the-counter remedies.",
        "specialty": "General Practice",
        "next_steps": "Monitor symptoms. Reassess if no improvement in 48 hours."
    },
    "Medium Urgency": {
        "care_type": "Schedule a primary care appointment.",
        "specialty": "Internal Medicine",
        "next_steps": "Book a check-up. Consider labs or further evaluation."
    },
    "High Urgency": {
        "care_type": "Seek immediate medical attention.",
        "specialty": "Emergency Medicine",
        "next_steps": "Go to the ER or urgent care center now."
    }
}

# Load trained model
model = joblib.load("models/caresense_model.pkl")

# Main classifier function
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
        "next_steps": enrichment["next_steps"]
    }
