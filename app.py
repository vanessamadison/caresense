import streamlit as st
from classifier import classify_symptom

st.title("CareSense – Your AI Check-In")

symptom_input = st.text_area("Describe your symptoms:")
if st.button("Check Urgency"):
    if symptom_input:
        label, score = classify_symptom(symptom_input)
        st.markdown(f"**Urgency Level:** `{label}` ({round(score * 100, 2)}%)")
    else:
        st.warning("Please enter a symptom description.")
