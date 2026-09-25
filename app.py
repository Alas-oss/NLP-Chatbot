import streamlit as st
import sys
sys.path.insert(0, "src")
from dialogue_manager import chat
from rate_limit import SlidingWindowLimiter
import config

st.title("NLP Chatbot")
st.caption("Answers come only from the indexed sources and link back to them.")

if "messages" not in st.session_state:
    st.session_state.messages = []  

if "rate_limiter" not in st.session_state:
    st.session_state.rate_limiter = SlidingWindowLimiter(
        max_events=config.RATE_LIMIT_MAX_MESSAGES,
        window_seconds=config.RATE_LIMIT_WINDOW_SECONDS,
    )


def show(msg: dict):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        for s in msg.get("sources", []):
            label = s["title"] + (f" - {s['section']}" if s.get("section") else "")
            st.markdown(f"[{s['id']}] " + (f"[{label}]({s['url']})" if s.get("url") else label))


for msg in st.session_state.messages:
    show(msg)

if prompt := st.chat_input("Ask a question -> "):
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    show(user_msg)

    if not st.session_state.rate_limiter.allow():
        wait = round(st.session_state.rate_limiter.retry_after())
        bot_msg = {"role": "assistant",
                   "content": f"{config.RATE_LIMIT_MESSAGE} (about {wait}s)", "sources": []}
        st.session_state.messages.append(bot_msg)
        show(bot_msg)
    else:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
        with st.spinner("Searching sources..."):
            result = chat(prompt, history)

        bot_msg = {"role": "assistant", "content": result.text,
                   "sources": [s.to_dict() for s in result.sources]}
        st.session_state.messages.append(bot_msg)
        show(bot_msg)