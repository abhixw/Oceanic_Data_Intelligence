import streamlit as st
import requests
import base64
from PIL import Image
import io
import pandas as pd
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr

# ----------------------------
# 1️⃣ PAGE CONFIG 
# ----------------------------
st.set_page_config(
    page_title="Oceanic Data Intelligence",
    layout="wide",
    page_icon="🌊"
)

# ----------------------------
# 2️⃣ GLOBAL STYLING 
# ----------------------------
st.markdown("""
<style>
body {
    background-color: #F8FAFC;
}

h1, h2, h3 {
    color: #1E3A8A;
}

.stButton>button {
    background-color: #1E3A8A;
    color: white;
    border-radius: 8px;
}

.stButton>button:hover {
    background-color: #10B981;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #E0F2FE;
}

.block-container {
    padding-top: 2rem;
}

.mic-nudge {
    margin-top: -30px;
}

.chat-nudge {
    margin-top: 27px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 3️⃣ LOAD DATA
# ----------------------------
df = pd.read_csv("data/train.csv")

# ----------------------------
# 4️⃣ HEADER
# ----------------------------
st.title("🌊 Oceanic Data Intelligence")
st.markdown("AI-Powered Titanic Dataset Analytics")

st.markdown("---")

# ----------------------------
# 5️⃣ SIDEBAR DATA PANEL
# ----------------------------
with st.sidebar:
    st.header("📊 Dataset Overview")
    st.metric("Total Records", df.shape[0])
    st.markdown("#### Columns")
    st.write(", ".join(df.columns))
    st.markdown("#### Preview")
    st.dataframe(df.head(10), use_container_width=True)

# ----------------------------
# 6️⃣ CHAT HISTORY
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in reversed(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("image"):
            st.image(message["image"], use_column_width=True)

# ----------------------------
# 7️⃣ HANDS-FREE VOICE LOGIC
# ----------------------------
def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    audio_data = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_data) as source:
        audio = r.record(source)
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return "Error: Speech recognition service is unavailable."

# ----------------------------
# 8️⃣ USER INPUT (BOTTOM)
# ----------------------------
voice_query = None

# Using columns for tighter horizontal alignment
col1, col2 = st.columns([0.03, 1], gap="small")
with col1:
    st.markdown('<div class="mic-nudge">', unsafe_allow_html=True)
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e74c3c",
        neutral_color="#1E3A8A",
        icon_name="microphone",
        icon_size="1x",
        pause_threshold=3.0,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chat-nudge">', unsafe_allow_html=True)
    prompt = st.chat_input("Ask about Titanic passengers...")
    st.markdown('</div>', unsafe_allow_html=True)

# Automatically process voice query if detected
if audio_bytes:
    with st.spinner("Analyzing voice..."):
        voice_query = transcribe_audio(audio_bytes)

if voice_query:
    prompt = voice_query

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔎 Analyzing data...")

        try:
            response = requests.post(
                "http://127.0.0.1:8000/ask",
                json={"question": prompt},
                timeout=300
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "No answer provided.")
                image_data = result.get("image")

                message_placeholder.markdown(answer)

                chat_entry = {"role": "assistant", "content": answer}

                if image_data:
                    img_bytes = base64.b64decode(image_data)
                    img = Image.open(io.BytesIO(img_bytes))
                    st.image(img, caption="Generated Visualization", use_column_width=True)
                    chat_entry["image"] = img

                st.session_state.messages.append(chat_entry)

            else:
                error_msg = f"Backend error: {response.status_code}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
