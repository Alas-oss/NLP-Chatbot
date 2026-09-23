import streamlit as st
import sys
sys.path.insert(0, "src")
from dialogue_manager import chat

st.title("NLP Chatbot")
st.caption("Answers come only from the indexed sources and link back to them.")

if "messages" not in st.session_state:
    st.session_state.messages = []   # {"role", "content", "sources"?}


def show(msg: dict):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        for s in msg.get("sources", []):
            label = s["title"] + (f" - {s['section']}" if s.get("section") else "")
            st.markdown(f"[{s['id']}] " + (f"[{label}]({s['url']})" if s.get("url") else label))


for msg in st.session_state.messages:
    show(msg)

if prompt := st.chat_input("Ask a question -> "):
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    show(user_msg)

    with st.spinner("Searching sources..."):
        result = chat(prompt, history)

    bot_msg = {"role": "assistant", "content": result.text,
               "sources": [s.to_dict() for s in result.sources]}
    st.session_state.messages.append(bot_msg)
    show(bot_msg)
