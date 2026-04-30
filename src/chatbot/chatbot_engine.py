import requests

BASE_OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_COACH_PROMPT = """
You are an empathetic, human-like ADHD productivity coach. 
Your primary goal is to have a natural, one-on-one, back-and-forth conversation.
Your coaching rules:
- Speak like a real human coach sitting across from them.
- Ask ONE clarifying or guiding question at a time and wait for their response.
- Do NOT give a long list of steps or a bulleted action plan unless explicitly asked.
- Validate their feelings briefly before asking your question.
- Keep responses to 1-3 short sentences.
- Avoid robotic bullet points or formatting.
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
            "It sounds like you're feeling pretty overwhelmed, which makes focus really hard. If we could pick just *one* tiny thing to knock out right now, what would it be?"
        )
    if any(keyword in prompt_lower for keyword in ["time", "schedule", "plan", "deadline", "routine"]):
        return (
            "Planning can definitely be tricky. Instead of looking at the whole schedule, what is the very next thing you need to do in the next 10 minutes?"
        )
    if any(keyword in prompt_lower for keyword in ["motivation", "procrast", "lazy", "energy"]):
        return (
            "It's totally normal to hit a wall with motivation. What if we just do a 2-minute 'starter' task? What's the smallest possible step you could take right now?"
        )
    return (
        "I hear you, and I'm here to help. What is the main thing you want us to tackle together today?"
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
