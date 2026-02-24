import streamlit as st
import requests
import base64
from PIL import Image
import io
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Titanic AI Assistant",
    page_icon="🚢",
    layout="wide"
)

# Custom CSS for a premium look
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .sidebar .sidebar-content {
        background-image: linear-gradient(#2e7fb8, #1c4e72);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚢 Titanic Dataset Chat Agent")
st.markdown("---")

# Sidebar for dataset overview
with st.sidebar:
    st.header("📊 Dataset Overview")
    try:
        # Data is in the root data folder
        df = pd.read_csv("data/train.csv")
        st.write(f"**Total Records:** {len(df)}")
        st.write("**Columns:**", ", ".join(df.columns))
        st.dataframe(df.head(10), use_container_width=True)
    except Exception as e:
        st.warning("Could not load dataset preview in sidebar.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("image"):
            st.image(message["image"])

# React to user input
if prompt := st.chat_input("Ask me about the Titanic passengers..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
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
                    # Decode and display image
                    img_bytes = base64.b64decode(image_data)
                    img = Image.open(io.BytesIO(img_bytes))
                    st.image(img, caption="Generated Visualization", use_column_width=True)
                    chat_entry["image"] = img
                
                st.session_state.messages.append(chat_entry)
            else:
                error_msg = f"Error: Backend returned status code {response.status_code}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
        except requests.exceptions.ConnectionError:
            error_msg = "Error: Could not connect to the backend server. Please ensure it is running on http://localhost:8000"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})