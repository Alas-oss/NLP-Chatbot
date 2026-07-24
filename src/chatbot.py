import sys
sys.path.insert(0, 'src')
import time 
from dialogue_manager import get_response

try:
    from rag_chain import langfuse
except Exception:
    langfuse = None

print("NLP Chatbot ready. Type 'quit'/'exit' to exit.")

try:
    while True: 
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        print("...", end="", flush=True)
        start = time.monotonic()
        try: 
            response = get_response(user_input)
        except Exception as e:
            print(f"\rSomething went wrong: {e}. Try again.")
            continue
        elapsed = time.monotonic() - start
        print(f"\r{response}\n[{elapsed:.1f}s]")

except KeyboardInterrupt:
    print("\nGoodbye!")

finally:
    if langfuse:
        langfuse.flush()