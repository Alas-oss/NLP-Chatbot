import sys
sys.path.insert(0, "src")
from dialogue_manager import chat, format_sources
from rag_chain import flush_traces

print("NLP Chatbot ready. Type 'quit'/'exit' to exit.")
history: list[dict] = []
while True:
    user_input = input("> ").strip()
    if not user_input:
        continue
    if user_input.lower() in ("quit", "exit"):
        print("Goodbye!")
        flush_traces()
        break
    result = chat(user_input, history)
    print(result.text)
    if result.sources:
        print("\nSources:\n" + format_sources(result.sources))
    history += [{"role": "user", "content": user_input},
                {"role": "assistant", "content": result.text}]
