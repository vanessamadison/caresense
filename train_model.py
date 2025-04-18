import os
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

df = pd.read_csv("data/extracted_symptoms_train.csv")

enriched_map = {
    "Dengue": {"urgency": "High Urgency", "care_type": "Fluids & monitoring", "specialty": "Infectious Disease"},
    "Pneumonia": {"urgency": "High Urgency", "care_type": "Antibiotics & rest", "specialty": "Pulmonology"},
    "Arthritis": {"urgency": "Medium Urgency", "care_type": "Anti-inflammatory meds", "specialty": "Rheumatology"},
    "Hypertension": {"urgency": "Medium Urgency", "care_type": "Lifestyle + medication", "specialty": "Cardiology"},
    "allergy": {"urgency": "Low Urgency", "care_type": "Antihistamines", "specialty": "Immunology"},
    "Acne": {"urgency": "Low Urgency", "care_type": "Topical treatment", "specialty": "Dermatology"},
    "Gastroesophageal Reflux Disease": {"urgency": "Medium Urgency", "care_type": "Diet changes + PPI", "specialty": "Gastroenterology"},
    "Common Cold": {"urgency": "Low Urgency", "care_type": "Rest & hydration", "specialty": "General Practice"},
    "Migraine": {"urgency": "Medium Urgency", "care_type": "Pain management", "specialty": "Neurology"},
    "Bronchial Asthma": {"urgency": "High Urgency", "care_type": "Inhalers, steroids", "specialty": "Pulmonology"},
}

df = df[df["disease"].isin(enriched_map.keys())]
df["urgency"] = df["disease"].map(lambda d: enriched_map[d]["urgency"])
df["care_type"] = df["disease"].map(lambda d: enriched_map[d]["care_type"])
df["specialty"] = df["disease"].map(lambda d: enriched_map[d]["specialty"])
df["urgency_encoded"] = df["urgency"].map({"Low Urgency": 0, "Medium Urgency": 1, "High Urgency": 2})

X = df["symptom_text"]
y = df["urgency_encoded"]

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(stop_words="english")),
    ("clf", LogisticRegression(max_iter=1000))
])
pipeline.fit(X_train, y_train)

os.makedirs("models", exist_ok=True)
joblib.dump(pipeline, "models/caresense_model.pkl")

print("✅ Model trained and saved to models/caresense_model.pkl")
