import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# 1. Jib l-list dyal l-models l-fabor men OpenRouter API
print("🔍 Searching for active FREE models on OpenRouter...")
models_response = requests.get("https://openrouter.ai/api/v1/models")

if models_response.status_code == 200:
    all_models = models_response.json()['data']
    # N-filtero ghir l-models li fihom :free
    free_models = [m['id'] for m in all_models if m['id'].endswith(':free')]
    
    print(f"✅ Found {len(free_models)} free models!")
    print("Top available free models:", free_models[:5])
    
    # Select the first available free model
    SELECTED_MODEL = free_models[0]
    print(f"\n🧪 Testing selected model: {SELECTED_MODEL}")
    
    # 2. Test request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": SELECTED_MODEL,
        "messages": [{"role": "user", "content": "Salam! Test message."}]
    }
    
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if res.status_code == 200:
        print(f"\n🎉 SUCCESS! Working model slug: {SELECTED_MODEL}\n")
        print("Response from AI:")
        print(res.json()['choices'][0]['message']['content'])
    else:
        print(f"❌ Failed to query model ({res.status_code}): {res.text}")
else:
    print("❌ Could not fetch models list.")