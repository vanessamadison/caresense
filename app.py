import streamlit as st
from classifier import classify_symptom

st.set_page_config(page_title="CareSense – Your AI Check-In", page_icon="🩺", layout="centered")
st.title("CareSense – Your AI Check-In")

st.markdown("Describe your symptoms below to receive an urgency estimate and care recommendation.")

symptom_input = st.text_area("Enter Your symptoms:", height=150)

if st.button("🔍 Check Urgency"):
    if symptom_input.strip():
        result = classify_symptom(symptom_input)

        st.markdown(f"### 🩺 Urgency Level: `{result['urgency']}` ({round(result['confidence'], 2)}%)")
        st.markdown(f"**💊 Recommended Care:** {result['care_type']}")
        st.markdown(f"**🏥 Suggested Specialty:** {result['specialty']}")

    else:
        st.warning("Please enter a symptom description.")

st.markdown("""
---
⚠️ *Disclaimer: This tool is for educational and experimental purposes only. It is not a substitute for professional medical advice. Always consult a licensed physician.*
""")
