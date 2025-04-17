import streamlit as st
from PIL import Image
import pytesseract
from classifier import classify_symptom

st.set_page_config(page_title="CareSense – AI Triage Assistant", layout="centered")
st.title("📤 Upload a Patient Symptom Report")

uploaded = st.file_uploader("Upload image (.png/.jpg):", type=["png", "jpg", "jpeg"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Uploaded Report", use_column_width=True)

    extracted = pytesseract.image_to_string(img)
    st.subheader("📝 Extracted Symptom Text")
    st.code(extracted)

    if st.button("🔍 Analyze Symptoms"):
        result = classify_symptom(extracted)

        st.markdown(f"## {result['tip']}  \n**Urgency Level:** {result['urgency']} ({result['confidence']}%)")
        st.markdown(f"**Recommended Care:** {result['care_type']}  \n**Suggested Specialty:** {result['specialty']}")
