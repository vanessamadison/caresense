import streamlit as st
from classifier import classify_symptom
from datetime import datetime
import pytz

# App config
st.set_page_config(
    page_title="CareSense – AI Symptom Assistant",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Styles
st.markdown("""
    <style>
        html, body, .reportview-container, .main {
            background-color: #0e1117;
            color: #e1e1e1;
            font-family: 'Segoe UI', sans-serif;
        }
        .subtitle {
            color: #cbd5e1;
            font-size: 18px;
            margin-bottom: 30px;
        }
        .card {
            background-color: #1a1d23;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            border: 1px solid #2f343f;
        }
        .urgency-high { color: #f87171; font-weight: bold; }
        .urgency-medium { color: #fbbf24; font-weight: bold; }
        .urgency-low { color: #34d399; font-weight: bold; }
        .progress-container {
            height: 12px;
            background-color: #2f343f;
            border-radius: 6px;
            overflow: hidden;
            margin: 8px 0 16px 0;
        }
        .progress-bar {
            height: 100%;
            transition: width 0.3s ease;
        }
    </style>
""", unsafe_allow_html=True)

# Logo and subtitle
st.image("assets/logo/caresense_logo_dark.png", width=220)
st.markdown("<div class='subtitle'>Your AI-powered symptom assistant. Confidential, smart, and caring.</div>", unsafe_allow_html=True)

# User input
symptom_input = st.text_area("Describe your symptoms:", height=150, placeholder="e.g. I have a burning chest pain that gets worse after eating...")

timestamp = datetime.now(pytz.timezone("US/Mountain")).strftime("%b %d, %Y at %I:%M %p")

# Handle user request
if st.button("Check Urgency"):
    if symptom_input.strip():
        result = classify_symptom(symptom_input)

        if "logs" not in st.session_state:
            st.session_state.logs = []

        st.session_state.logs.append({
            "text": symptom_input,
            "timestamp": timestamp,
            "urgency": result["urgency"],
            "confidence": round(result["confidence"], 2)
        })

        urgency_color = {
            "High Urgency": "#f87171",
            "Medium Urgency": "#fbbf24",
            "Low Urgency": "#34d399"
        }[result["urgency"]]

        urgency_class = {
            "High Urgency": "urgency-high",
            "Medium Urgency": "urgency-medium",
            "Low Urgency": "urgency-low"
        }[result["urgency"]]

        confidence_percent = round(result["confidence"], 2)

        # Show results
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>Assessment Result</h4>", unsafe_allow_html=True)

        # Confidence bar
        st.markdown(f"""
            <div class="progress-container">
                <div class="progress-bar" style="width: {confidence_percent}%; background-color: {urgency_color};"></div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**Urgency:** <span class='{urgency_class}'>{result['urgency']}</span> ({confidence_percent}%)", unsafe_allow_html=True)
        st.markdown(f"**Recommended Care:** {result['care_type']}")
        st.markdown(f"**Suggested Specialty:** {result['specialty']}")

        # Add insight if this symptom is repeating
        if any(log["text"] == symptom_input and log["urgency"] != "Low Urgency" for log in st.session_state.logs[:-1]):
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("**CareSense Insight:** This symptom has been reported more than once. Consider discussing this pattern with a provider.")

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Please enter a symptom description.")

# History section
if "logs" in st.session_state and st.session_state.logs:
    st.markdown("<h4 style='margin-top: 40px;'>Recent Symptom History</h4>", unsafe_allow_html=True)

    for entry in reversed(st.session_state.logs[-5:]):
        bg_color = {
            "High Urgency": "#2f1e1e",
            "Medium Urgency": "#2f2617",
            "Low Urgency": "#1d2f25"
        }[entry["urgency"]]

        border_color = {
            "High Urgency": "#f87171",
            "Medium Urgency": "#fbbf24",
            "Low Urgency": "#34d399"
        }[entry["urgency"]]

        st.markdown(f"""
        <div style='
            background-color: {bg_color};
            border-left: 4px solid {border_color};
            padding: 16px;
            border-radius: 6px;
            margin: 10px 0;
            line-height: 1.6;
        '>
            <span style='color: #9ca3af; font-size: 14px;'>{entry['timestamp']}</span><br>
            <span style='font-size: 15px;'>{entry['text']}</span><br>
            <strong style='color: {border_color};'>[{entry['urgency']}]</strong>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("""---  
*This app is for educational and experimental use only. Always consult a licensed physician before making medical decisions.*
""")
