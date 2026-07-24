import streamlit as st
import sys
import time
sys.path.insert(0, "src")
from dialogue_manager import get_response

st.set_page_config(
    page_title="Knowledge Chatbot",
    page_icon="💬",
    layout="centered",
)

with st.sidebar:
    st.header("About")
    st.write(
        "This chatbot answers questions using retrieval-augmented generation — "
        "it searches a knowledge base for relevant passages before answering, "
        "rather than relying on general knowledge alone."
    )
    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption(f"{len(st.session_state.get('messages', []))} messages this session")

st.title("💬 Knowledge Chatbot")
st.caption("Ask a question — answers are grounded in a specific knowledge base, not general guesswork.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "💬"
    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="👤").write(prompt)

    with st.chat_message("assistant", avatar="💬"):
        with st.spinner("Searching knowledge base..."):
            try:
                start = time.monotonic()
                response = get_response(prompt)
                elapsed = time.monotonic() - start
            except Exception as e:
                response = f"Something went wrong while generating a response: {e}"
                elapsed = None
        st.write(response)
        if elapsed is not None:
            st.caption(f"Answered in {elapsed:.1f}s")

    st.session_state.messages.append({"role": "assistant", "content": response})