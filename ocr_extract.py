import os
import csv
import pandas as pd
from PIL import Image
import pytesseract

image_dir = "data/Symptom2Disease_dataset_train"
label_csv = "data/Symptom2Disease_dataset_train.csv"
output_csv = "data/extracted_symptoms_train.csv"

labels_df = pd.read_csv(label_csv, header=None, names=["file_name", "disease"])
labels_dict = dict(zip(labels_df["file_name"], labels_df["disease"]))

def extract_symptoms(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        if "Symptoms:" in text:
            return text.split("Symptoms:")[-1].strip()
        return text.strip()
    except Exception as e:
        print(f"Error reading {image_path}: {e}")
        return ""

with open(output_csv, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["symptom_text", "disease"])
    
    for filename in os.listdir(image_dir):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            full_path = os.path.join(image_dir, filename)
            extracted = extract_symptoms(full_path)
            label = labels_dict.get(f"Symptom2Disease_dataset_train/{filename}", "Unknown")
            if extracted and label != "Unknown":
                writer.writerow([extracted, label])

print(f"✅ Extracted data written to {output_csv}")
