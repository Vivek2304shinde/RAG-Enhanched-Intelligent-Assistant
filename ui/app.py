# ui/app.py
import streamlit as st
from streamlit_audiorec import st_audiorec
import requests
import json

API_URL = "http://localhost:8000"

st.set_page_config(page_title="BFIA - Voice AI Assistant", layout="wide")
st.title("🎤 BFIA - Voice Financial Intelligence Agent")
st.markdown("Ask questions about Indian finance using voice or text.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []  # for display
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []  # for API

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "audio_url" in msg:
            st.audio(msg["audio_url"], format="audio/mpeg")

# Voice input
st.sidebar.header("🎤 Voice Input")
audio_bytes = st_audiorec()
if audio_bytes:
    with st.spinner("Transcribing..."):
        files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
        resp = requests.post(f"{API_URL}/asr", files=files)
        if resp.status_code == 200:
            query_text = resp.json()["text"]
            st.success(f"Recognized: {query_text}")
            # Process the query as if typed
            process_query(query_text)

# Text input
if prompt := st.chat_input("Type your question..."):
    process_query(prompt)

def process_query(query_text):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": query_text})
    with st.chat_message("user"):
        st.markdown(query_text)

    # Add to conversation history for API
    st.session_state.conversation_history.append({"role": "user", "content": query_text})

    # Call /query with full history
    payload = {
        "query": query_text,
        "history": st.session_state.conversation_history
    }
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{API_URL}/query", json=payload)
                response.raise_for_status()
                data = response.json()
                answer = data["answer"]
                citations = data.get("citations", [])
                hallucination = data.get("hallucination_score")

                # Display answer
                display_text = answer
                if hallucination is not None:
                    display_text += f"\n\n*Hallucination score: {hallucination:.2f}*"
                if citations:
                    display_text += "\n\n**Sources:**\n"
                    for i, c in enumerate(citations, 1):
                        display_text += f"{i}. {c['title']} (page {c['page']})\n"
                st.markdown(display_text)

                # TTS – get audio
                tts_response = requests.post(f"{API_URL}/tts", data={"text": answer})
                if tts_response.status_code == 200:
                    audio_url = f"data:audio/mpeg;base64,{tts_response.content.hex()}"  # or use st.audio with bytes
                    st.audio(tts_response.content, format="audio/mpeg")

                # Save to conversation history
                st.session_state.conversation_history.append({"role": "assistant", "content": answer})
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"Error: {e}")