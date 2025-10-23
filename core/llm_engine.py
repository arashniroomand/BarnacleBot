
# === FILE: core/llm_engine.py ===
from huggingface_hub import InferenceClient
from .history_manager import load_history
from keys import API_KEY, SYSTEM_PROMPT


def _build_messages(user_id: str, question: str, tail_len: int = 6):
    history = load_history()
    user = history.get(user_id, {})
    conv = user.get("conversations", [])
    words = user.get("important_words", [])
    mode = user.get("mode", "normal")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # soft injection of important words if learning mode
    if mode == "learning" and words:
        # limit length to avoid token bloat
        sample = words[:8]
        injection = (
            "NOTE: The user wants to practice the following important words/phrases. "
            "When natural, use up to 2 of them per reply and wrap the used phrase in **bold**. "
            f"Words: {', '.join(sample)}."
        )
        messages.append({"role": "system", "content": injection})

    # append conversation tail (user/assistant pairs)
    tail = conv[-tail_len:] if isinstance(conv, list) else []
    for e in tail:
        messages.append({"role": "user", "content": e.get("user", "")})
        messages.append({"role": "assistant", "content": e.get("bot", "")})

    messages.append({"role": "user", "content": question})
    return messages


def chat_completion(user_id: str, question: str):
    client = InferenceClient(provider="novita", api_key=API_KEY)
    messages = _build_messages(user_id, question)

    completion = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        messages=messages,
        max_tokens=200,
        temperature=0.85,
        top_p=0.95
    )

    # defensive access
    try:
        return completion.choices[0].message.content.strip()
    except Exception:
        # fallback: try to stringify
        return str(completion)
