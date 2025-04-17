from PIL import Image
import pytesseract
import os
import csv
import random

# 🔍 Extracts text from an image using Tesseract OCR
def extract_symptoms_from_image(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    if "Symptoms:" in text:
        return text.split("Symptoms:")[-1].strip()
    return text.strip()

# 📁 Folder where patient report images are stored
report_folder = "data/reports"

# 📄 Output CSV
output_csv = "data/symptoms_from_images.csv"

# Get all image files in the folder
image_files = [f for f in os.listdir(report_folder) if f.endswith((".png", ".jpg", ".jpeg"))]

# 📥 Create CSV and write header
with open(output_csv, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["symptom_text", "urgency"])  # Add more fields later if needed

    for f in image_files:
        image_path = os.path.join(report_folder, f)
        extracted = extract_symptoms_from_image(image_path)

        # 🎲 Random urgency for demo/testing
        urgency_levels = ["Low Urgency", "Medium Urgency", "High Urgency"]
        urgency = random.choice(urgency_levels)

        writer.writerow([extracted, urgency])

print(f"✅ Extracted {len(image_files)} files and wrote to {output_csv}")
