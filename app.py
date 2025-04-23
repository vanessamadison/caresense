import streamlit as st
from classifier import classify_symptom
from datetime import datetime
import pytz

# Set up the app appearance and metadata
st.set_page_config(
    page_title="CareSense – AI Symptom Assistant",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Add dark mode styling with a clean, calming look
st.markdown("""
    <style>
        html, body, .reportview-container, .main {
            background-color: #0e1117;
            color: #e1e1e1;
            font-family: 'Segoe UI', sans-serif;
        }
        .title {
            color: #38bdf8;
            font-size: 32px;
            font-weight: 700;
            padding-top: 10px;
        }
        .subtitle {
            color: #cbd5e1;
            font-size: 18px;
            margin-bottom: 20px;
        }
        .card {
            background-color: #1a1d23;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            border: 1px solid #2f343f;
        }
        .urgency-high {
            color: #f87171;
            font-weight: bold;
        }
        .urgency-medium {
            color: #fbbf24;
            font-weight: bold;
        }
        .urgency-low {
            color: #34d399;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Logo and subtitle (safe for local use)
st.image("assets/logo/caresense_logo_dark.png", width=220)

st.markdown("<div style='color: #cbd5e1; font-size: 18px; margin-bottom: 20px;'>"
            "Your AI-powered symptom assistant. Confidential, smart, and caring."
            "</div>", unsafe_allow_html=True)


# Let user input their symptoms
symptom_input = st.text_area("Describe your symptoms:", height=150, placeholder="e.g. I have a burning chest pain that gets worse after eating...")

# Get current time for logs
timestamp = datetime.now(pytz.timezone("US/Mountain")).strftime("%b %d, %Y at %I:%M %p")

# Classify symptoms and log result
if st.button("Check Urgency"):
    if symptom_input.strip():
        result = classify_symptom(symptom_input)

        if "logs" not in st.session_state:
            st.session_state.logs = []

        st.session_state.logs.append({
            "text": symptom_input,
            "timestamp": timestamp,
            "urgency": result["urgency"]
        })

        # Style urgency with colors
        urgency_class = {
            "High Urgency": "urgency-high",
            "Medium Urgency": "urgency-medium",
            "Low Urgency": "urgency-low"
        }[result["urgency"]]

        # Show results
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>Assessment Result</h4>", unsafe_allow_html=True)
        st.markdown(f"<b>Urgency:</b> <span class='{urgency_class}'>{result['urgency']}</span> ({round(result['confidence'], 2)}%)", unsafe_allow_html=True)
        st.markdown(f"<b>Recommended Care:</b> {result['care_type']}")
        st.markdown(f"<b>Suggested Specialty:</b> {result['specialty']}")

        # Add insight if symptom is recurring
        if any(log["text"] == symptom_input and log["urgency"] != "Low Urgency" for log in st.session_state.logs[:-1]):
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("**CareSense Insight:** This symptom has been reported more than once. Consider discussing this pattern with a provider.", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Please enter a symptom description.")

# Show recent symptom history
if "logs" in st.session_state and st.session_state.logs:
    st.markdown("<h4 style='margin-top: 40px;'>Recent Symptom History</h4>", unsafe_allow_html=True)
    for entry in reversed(st.session_state.logs[-5:]):
        color = {
            "High Urgency": "#f87171",
            "Medium Urgency": "#fbbf24",
            "Low Urgency": "#34d399"
        }[entry["urgency"]]
        st.markdown(
            f"<div style='color:{color}; padding: 4px 0;'>{entry['timestamp']} — {entry['text']} [{entry['urgency']}]</div>",
            unsafe_allow_html=True
        )

# Footer disclaimer
st.markdown("""---  
*This app is for educational and experimental use only. Always consult a licensed physician before making medical decisions.*
""")
