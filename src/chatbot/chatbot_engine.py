import requests

BASE_OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_COACH_PROMPT = """
You are an ADHD-first productivity coach.
You support people with ADHD by giving short, adaptive coaching.
Your responses should be:
- concise and empathetic
- ADHD-specific
- focused on micro-actions (2-5 minute tasks)
- include a motivational nudge
- acknowledge streaks and progress when available
- offer adaptive task breakdowns instead of generic advice

Always keep responses under 4 sentences and avoid overwhelming the user.
"""


def build_coach_prompt(user_input, scores=None, user_data=None):
    user_stats = user_data or {}
    score_text = scores or {}
    streak_text = f"Current streak: {score_text.get('streak_days', 'N/A')} days." if score_text else ""
    risk_hint = "High focus risk detected." if score_text.get("adhd_risk", 0) >= 0.7 else ""

    prompt = f"""
{SYSTEM_COACH_PROMPT}

User stats:
{user_stats}

Score summary:
{score_text}
{streak_text}
{risk_hint}

Current challenge:
{user_input}

Task request:
- If the user is stuck, provide a single micro-action.
- If the user needs planning, break the next task into 2-3 tiny steps.
- If the user is distracted, suggest a short 10-minute sprint and one quick change.
- If mental health is a concern, offer a reflection prompt.

Response style:
- supportive
- clear
- ADHD-friendly
- action-oriented
"""
    return prompt


def generate_offline_reply(prompt):
    prompt_lower = prompt.lower()
    if any(keyword in prompt_lower for keyword in ["focus", "distract", "attention", "overwhelm", "concentration"]):
        return (
            "I can help with ADHD-friendly focus support. Start with one tiny step, set a 5-minute timer, and remove one distraction. "
            "That small win is your momentum."
        )
    if any(keyword in prompt_lower for keyword in ["time", "schedule", "plan", "deadline", "routine"]):
        return (
            "Use a tiny time block first. Pick one simple task, do it for 5 minutes, then celebrate the small win. "
            "That is your ADHD-friendly plan."
        )
    if any(keyword in prompt_lower for keyword in ["motivation", "procrast", "lazy", "energy"]):
        return (
            "Motivation often follows action. Choose the smallest step you can do in 2-3 minutes, then start it now. "
            "You’ve already made progress by asking for help."
        )
    return (
        "I’m here to help with ADHD-friendly strategies. Pick one tiny action, set a short timer, and I’ll keep you moving. "
        "Tell me what your next task is and I’ll break it down."
    )


def query_ollama(prompt, timeout=30):
    """
    Query Ollama API with a prompt.
    
    Args:
        prompt: str - The prompt to send to Ollama
        timeout: int - Request timeout in seconds
        
    Returns:
        str - Response from Ollama, or fallback reply if request fails
    """
    payload = {
        "model": "llama3:instruct",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(BASE_OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        return result.get("response", generate_offline_reply(prompt))
    except requests.exceptions.Timeout:
        return generate_offline_reply(prompt)
    except requests.exceptions.RequestException:
        return generate_offline_reply(prompt)
    except Exception:
        return generate_offline_reply(prompt)


def respond_to_query(user_input, history):
    """
    Generate a response to a user query using Ollama.
    
    Args:
        user_input: str - The user's message
        history: list - Previous conversation history
        
    Returns:
        str - Chatbot response
    """
    prompt = build_coach_prompt(user_input)
    return query_ollama(prompt)


def chatbot_response(user_input, scores=None, user_data=None):
    """
    Generate a personalized chatbot response.
    
    Args:
        user_input: str - User's message
        scores: dict - User's current scores
        user_data: dict - User's profile data
        
    Returns:
        str - Personalized response from chatbot
    """
    prompt = build_coach_prompt(user_input, scores=scores, user_data=user_data)
    payload = {
        "model": "llama3:instruct",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(BASE_OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get("response", generate_offline_reply(prompt))
    except requests.exceptions.Timeout:
        return generate_offline_reply(prompt)
    except requests.exceptions.RequestException:
        return generate_offline_reply(prompt)
    except Exception:
        return generate_offline_reply(prompt)
