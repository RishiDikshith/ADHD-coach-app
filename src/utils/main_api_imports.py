import os
import logging
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)

STRESS_KEYWORDS = {
    "stress", "stressed", "overwhelm", "overwhelmed", "anxious", "panic",
    "too much", "hard", "stuck", "tired", "sad", "depressed", "burned out",
    "tension", "tense", "cant focus", "can't focus", "cant understand", "can't understand"
}
POSITIVE_KEYWORDS = {
    "happy", "great", "good", "awesome", "fantastic", "amazing", "productive",
    "done", "finished", "excited", "glad", "joy", "better", "calm", "relaxed"
}
PRODUCTIVE_KEYWORDS = {
    "productive", "done", "finished", "completed", "focused", "progress",
    "did it", "working", "achieved", "accomplished", "on track", "next"
}
UNPRODUCTIVE_KEYWORDS = {
    "distracted", "procrastinating", "lazy", "unproductive", "cant focus",
    "can't focus", "behind", "stuck", "failing", "off track", "cant understand", "can't understand"
}

def generate_offline_reply(prompt):
    prompt_lower = prompt.lower()
    if any(kw in prompt_lower for kw in ["focus", "distract", "attention", "overwhelm", "concentration"]):
        reply = """REPLY:
Hey there! It sounds like you're feeling pretty overwhelmed right now, which makes focusing incredibly difficult. That's completely normal and okay! 🌬️

Sometimes our brains just need a tiny reset before diving back in. Let's take it slow and try not to force it.

If we could pick just *one* super tiny thing to knock out right now, what would it be? 🤔

TASKS:
- Take 3 deep breaths
- Open your notes
- Start a 5-minute timer"""
    elif any(kw in prompt_lower for kw in ["time", "schedule", "plan", "deadline", "routine"]):
        reply = """REPLY:
Planning can definitely be tricky, especially when there's so much on your plate! 🗓️

Instead of looking at the whole schedule and getting stressed, let's just zoom in on right now.

What is the very next thing you need to do in the next 10 minutes to feel a little better? ⏳

TASKS:
- Log your energy level
- clear your workspace
- Do a 2-minute focus sprint"""
    else:
        reply = """REPLY:
I hear you, and I completely understand where you're coming from. I'm right here to support you! 🤝

Let's figure this out together step by step so it doesn't feel like too much.

What is the main thing you want us to tackle together today? 🚀

TASKS:
- Define your main goal for today
- Break it into 3 small steps
- Start the first step"""
    return reply

MAX_CONCURRENT_AI_REQUESTS = int(os.getenv("MAX_CONCURRENT_AI_REQUESTS", "4"))
ai_queue_semaphore = threading.Semaphore(MAX_CONCURRENT_AI_REQUESTS)

@lru_cache(maxsize=1000)
def get_ai_reply(prompt, language: str = "en"):
    acquired = ai_queue_semaphore.acquire(timeout=15.0)
    if not acquired:
        return generate_offline_reply(prompt)
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return generate_offline_reply(prompt)
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", temperature=0.7, max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as exc:
        logger.error("Groq API request failed: %s", exc)
        return generate_offline_reply(prompt)
    finally:
        ai_queue_semaphore.release()
