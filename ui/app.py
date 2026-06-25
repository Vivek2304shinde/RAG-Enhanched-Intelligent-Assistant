# ui/app.py
import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"  # change for production

st.set_page_config(page_title="BFIA - Bharat Financial Intelligence Agent", layout="wide")
st.title("🇮🇳 BFIA - Financial Intelligence Agent")
st.markdown("Ask about RBI, SEBI, GST, Budgets, Schemes, and more.")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{API_URL}/query", json={"query": prompt})
                response.raise_for_status()
                data = response.json()
                answer = data["answer"]
                citations = data.get("citations", [])
                hallucination = data.get("hallucination_score")
                if hallucination is not None:
                    answer += f"\n\n*Hallucination score: {hallucination:.2f}*"
                if citations:
                    answer += "\n\n**Sources:**\n"
                    for i, c in enumerate(citations, 1):
                        answer += f"{i}. {c['title']} (page {c['page']})\n"
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Error: {e}")