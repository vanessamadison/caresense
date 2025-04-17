from transformers import pipeline

# Initialize the zero-shot classification pipeline
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify_symptom(text):
    labels = ["Low Urgency", "Medium Urgency", "High Urgency"]
    result = classifier(text, labels)
    return result["labels"][0], result["scores"][0]
