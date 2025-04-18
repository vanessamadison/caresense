import streamlit as st
from classifier import classify_symptom

# Set page config
st.set_page_config(page_title="CareSense – Your AI Check-In", page_icon="🩺", layout="centered")

# Custom CSS Styling
st.markdown("""
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
        }
        .title {
            color: #0d6efd;
            font-size: 32px;
            font-weight: 700;
            padding-top: 10px;
        }
        .box {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            border: 1px solid #dee2e6;
        }
        .urgent-high {
            color: red;
            font-weight: bold;
        }
        .urgent-medium {
            color: orange;
            font-weight: bold;
        }
        .urgent-low {
            color: green;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<div class='title'>CareSense – Your AI Check-In</div>", unsafe_allow_html=True)
st.markdown("Describe your symptoms below to receive an urgency estimate and care recommendation.")

# Input box
symptom_input = st.text_area("Enter your symptoms:", height=150)

# Run prediction
if st.button("🔍 Check Urgency"):
    if symptom_input.strip():
        result = classify_symptom(symptom_input)

        # Styling by urgency level
        urgency_class = {
            "High Urgency": "urgent-high",
            "Medium Urgency": "urgent-medium",
            "Low Urgency": "urgent-low"
        }[result['urgency']]

        # Display results
        st.markdown(f"<div class='box'>", unsafe_allow_html=True)
        st.markdown(f"### Urgency Level: <span class='{urgency_class}'>{result['urgency']}</span> ({round(result['confidence'], 2)}%)", unsafe_allow_html=True)
        st.markdown(f"**Recommended Care:** {result['care_type']}")
        st.markdown(f"**Suggested Specialty:** {result['specialty']}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Generate shareable result text
        result_text = f"""
CareSense Report
====================
Symptoms: {symptom_input}

Urgency Level: {result['urgency']} ({round(result['confidence'], 2)}%)
Recommended Care: {result['care_type']}
Suggested Specialty: {result['specialty']}
"""

        # # Download option
        # st.download_button(
        #     label="Download Report",
        #     data=result_text,
        #     file_name="caresense_report.txt",
        #     mime="text/plain"
        # )

        # Email share
        subject = "CareSense Symptom Report"
        body = result_text.replace('\n', '%0A')  # URL encode line breaks
        mailto_url = f"mailto:?subject={subject}&body={body}"

        st.markdown(f"""
            <a href="{mailto_url}" target="_blank">
                <button style="
                    background-color:#007bff;
                    color:white;
                    border:none;
                    padding:8px 16px;
                    font-size:14px;
                    border-radius:5px;
                    cursor:pointer;
                    margin-top:10px;
                ">
                Share via Email
                </button>
            </a>
        """, unsafe_allow_html=True)

    else:
        st.warning("Please enter a symptom description.")

# Disclaimer
st.markdown("""---  
⚠️ *Disclaimer: This tool is for educational and experimental purposes only. It is not a substitute for professional medical advice. Always consult a licensed physician.*
""")
