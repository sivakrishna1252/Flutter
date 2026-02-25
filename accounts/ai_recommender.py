from django.conf import settings
import json
from openai import OpenAI
from urllib.parse import quote
import httpx

# Initialize OpenAI client lazily
_client = None

def get_openai_client():
    """Get or initialize the OpenAI client with robust configuration lookup"""
    global _client
    
    if _client is not None:
        return _client
    
    import os

    try:
        api_key = getattr(settings, "OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        base_url = getattr(settings, "OPENAI_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"))
    except Exception as e:
        print(f"DEBUG: Error accessing settings: {e}")
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    if not api_key:
        print("DEBUG ERROR: OPENAI_API_KEY is empty/missing")
        return None
    
    try:
        # Create a custom httpx client to avoid "proxies" TypeError on Windows/Python 3.13
        http_client = httpx.Client(
            base_url=base_url,
            follow_redirects=True,
        )

        client_kwargs = {
            "api_key": api_key,
            "base_url": base_url,
            "http_client": http_client,
        }
        
        _client = OpenAI(**client_kwargs)
        print(f"✓ Groq client initialized. Key starts with: {api_key[:10]}...")
        return _client
    except Exception as e:
        print(f"✗ Failed to initialize AI client: {e}")
        return None

def get_fallback_image_url(item_name):
    """Generate fallback image URL using Unsplash"""
    search_query = quote(item_name.split()[0] if item_name else "food")
    return f"https://source.unsplash.com/400x400/?{search_query},food"

def generate_meal_image(prompt):
   
    try:
        client = get_openai_client()
        if not client or not prompt:
            return get_fallback_image_url(prompt)
        
        image_model = getattr(settings, "OPENAI_IMAGE_MODEL_NAME", "stabilityai/stable-diffusion-xl-base-1.0")
        
        response = client.images.generate(
            model=image_model,
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print(f"Image generation failed: {e}")
        return get_fallback_image_url(prompt[:20] if prompt else "food")

def generate_item_image_prompt(item_name, item_serving):
    """Generate a detailed image prompt for a meal item"""
    return f"Professional food photography of {item_name} ({item_serving}), appetizer presentation, studio lighting"

def recommend_meals_for_user(profile, meal_type: str):
    """Main function to recommend meals using AI"""
    client = get_openai_client()
    if not client:
        return {"items": [], "error": "AI client not configured."}

    model_name = getattr(settings, "OPENAI_MODEL_NAME", "llama-3.3-70b-versatile")

    user_data = {
        "name": profile.name,
        "age": profile.age,
        "weight": profile.weight,
        "height_cm": profile.height_cm,
        "gender": profile.gender,
        "goal": profile.goal,
        "diet_preference": profile.diet_preference,
        "health_conditions": profile.health_conditions or [],
        "allergies": profile.allergies or [],
    }

    def clean_numeric(val):
        """Helper to ensure macro values are single numbers, not ranges or strings with units"""
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            import re
            # Handle ranges like "250-300" by taking the average
            if "-" in val:
                nums = re.findall(r"\d+\.?\d*", val)
                if len(nums) >= 2:
                    try:
                        return int((float(nums[0]) + float(nums[1])) / 2.0)
                    except:
                        pass
            # Just take the first number found
            nums = re.findall(r"\d+\.?\d*", val)
            if nums:
                try:
                    return int(float(nums[0]))
                except:
                    pass
        return 0

    system_prompt = (
        "You are a nutritionist. Suggest suitable Indian food options for one meal. "
        "Respect diet_preference, health_conditions, and allergies. "
        "Respond ONLY as JSON: { 'items': [ { 'name', 'serving', 'calories', 'protein_g', 'carbs_g', 'fats_g', 'note' } ], "
        "'image_prompt': 'desc' }. "
        "IMPORTANT: 'calories', 'protein_g', 'carbs_g', and 'fats_g' MUST be single numeric integers. "
        "NO DECIMALS (e.g., use 15 instead of 15.5). "
        "DO NOT use ranges like '250-300' or include 'g' or 'kcal' in these numeric fields."
    )

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"meal_type": meal_type, "user": user_data})},
            ],
            temperature=0.5,
        )
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        items = data.get("items", [])
    except Exception as e:
        print(f"Error calling AI: {e}")
        return {"items": [], "error": f"Failed to generate: {str(e)}"}

    cleaned = []
    for item in items[:8]:
        cleaned.append({
            "name": item.get("name", ""),
            "serving": item.get("serving", ""),
            "calories": clean_numeric(item.get("calories", 0)),
            "protein_g": clean_numeric(item.get("protein_g", 0)),
            "carbs_g": clean_numeric(item.get("carbs_g", 0)),
            "fats_g": clean_numeric(item.get("fats_g", 0)),
            "note": item.get("note", ""),
            "image_url": get_fallback_image_url(item.get("name", "")) # Using fallback for speed
        })

    return {"items": cleaned, "image_url": get_fallback_image_url(meal_type)}
