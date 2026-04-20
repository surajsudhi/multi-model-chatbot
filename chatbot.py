import anthropic
from openai import OpenAI
from google import genai
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ── Clients ──────────────────────────────────────────────
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_PROMPT = "You are a helpful, concise assistant."
AVAILABLE_MODELS = ["claude", "gpt4o", "gemini"]

# ── Core chat function ────────────────────────────────────
def chat(model: str, history: list, user_message: str) -> str:
    history.append({"role": "user", "content": user_message})

    if model == "claude":
        response = claude_client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history
        )
        reply = response.content[0].text

    elif model == "gpt4o":
        messages_with_system = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages_with_system
        )
        reply = response.choices[0].message.content

    elif model == "gemini":
        contents = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in history
        )
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=f"{SYSTEM_PROMPT}\n\n{contents}"
        )
        reply = response.text

    history.append({"role": "assistant", "content": reply})
    return reply

# ── Persistence ───────────────────────────────────────────
def save_history(history: list):
    with open("chat_history.json", "w") as f:
        json.dump({"saved_at": datetime.now().isoformat(), "history": history}, f, indent=2)
    print("[Session saved to chat_history.json]")

def load_history() -> list:
    if os.path.exists("chat_history.json"):
        with open("chat_history.json") as f:
            data = json.load(f)
        print(f"[Loaded {len(data['history'])} messages from previous session]")
        return data["history"]
    return []

# ── Main loop ─────────────────────────────────────────────
def main():
    print("\n🤖 Multi-Model Chatbot")
    print(f"Models: {', '.join(AVAILABLE_MODELS)}")
    print("Commands: /switch <model> | /save | /load | /history | /quit\n")

    current_model = "claude"
    history = []

    if os.path.exists("chat_history.json"):
        choice = input("Previous session found. Load it? (y/n): ").strip().lower()
        if choice == "y":
            history = load_history()

    while True:
        try:
            user_input = input(f"\n[{current_model}] You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.startswith("/switch"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1] in AVAILABLE_MODELS:
                current_model = parts[1]
                print(f"[Switched to {current_model} — history preserved]")
            else:
                print(f"[Available models: {', '.join(AVAILABLE_MODELS)}]")

        elif user_input == "/save":
            save_history(history)

        elif user_input == "/load":
            history = load_history()

        elif user_input == "/history":
            for msg in history:
                print(f"  {msg['role'].upper()}: {msg['content'][:80]}...")

        elif user_input == "/quit":
            save_history(history)
            break

        else:
            try:
                reply = chat(current_model, history, user_input)
                print(f"\n{current_model.upper()}: {reply}")
            except Exception as e:
                print(f"[Error: {e}]")

if __name__ == "__main__":
    main()