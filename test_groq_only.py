import os
from dotenv import load_dotenv

# Load variables from your .env file
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ ERROR: GROQ_API_KEY not found!")
    print("Please make sure you have added GROQ_API_KEY=gsk_... to your .env file.")
    exit()

print("🔑 Found GROQ_API_KEY! Sending a test message to the cloud...\n")

try:
    from groq import Groq
    client = Groq(api_key=api_key)
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": "Hi Coach! I have 3 tasks to do but I'm feeling paralyzed. Give me one short tip to start."}],
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=1024,
    )
    print("✅ SUCCESS! Here is Groq's lightning-fast response:\n")
    print("🤖 " + chat_completion.choices[0].message.content)
except Exception as e:
    print(f"❌ ERROR connecting to Groq: {e}")