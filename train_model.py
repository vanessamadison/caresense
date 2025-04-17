import os
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# STEP 1: Enriched Labels Map
enriched_map = {
    "Dengue": {"urgency": "High Urgency", "care_type": "Fluids & monitoring", "specialty": "Infectious Disease"},
    "Pneumonia": {"urgency": "High Urgency", "care_type": "Antibiotics & rest", "specialty": "Pulmonology"},
    "Arthritis": {"urgency": "Medium Urgency", "care_type": "Anti-inflammatory meds", "specialty": "Rheumatology"},
    "Hypertension": {"urgency": "Medium Urgency", "care_type": "Lifestyle + medication", "specialty": "Cardiology"},
    "allergy": {"urgency": "Low Urgency", "care_type": "Antihistamines", "specialty": "Immunology"},
    "Acne": {"urgency": "Low Urgency", "care_type": "Topical treatment", "specialty": "Dermatology"},
}

# STEP 2: Load CSV
df = pd.read_csv("data/Symptom2Disease_dataset_train.csv", header=None, names=["image_path", "Diagnosis"])

# STEP 3: Filter by only mapped diseases
df = df[df["Diagnosis"].isin(enriched_map.keys())]

# STEP 4: Add Enriched Columns
df["urgency"] = df["Diagnosis"].map(lambda d: enriched_map[d]["urgency"])
df["care_type"] = df["Diagnosis"].map(lambda d: enriched_map[d]["care_type"])
df["specialty"] = df["Diagnosis"].map(lambda d: enriched_map[d]["specialty"])
df["symptom_text"] = df["Diagnosis"] + " symptoms"

# STEP 5: Encode target
urgency_map = {"Low Urgency": 0, "Medium Urgency": 1, "High Urgency": 2}
df["urgency_encoded"] = df["urgency"].map(urgency_map)

# STEP 6: Train
X = df["symptom_text"]
y = df["urgency_encoded"]

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(stop_words="english")),
    ("clf", LogisticRegression(max_iter=1000))
])
pipeline.fit(X_train, y_train)

# STEP 7: Save model
os.makedirs("models", exist_ok=True)
joblib.dump(pipeline, "models/caresense_model.pkl")

print("✅ Model trained and saved to models/caresense_model.pkl")
