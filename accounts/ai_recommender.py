

import os
import json
from openai import OpenAI
from urllib.parse import quote

# Initialize OpenAI client lazily with proper error handling
_client = None

def get_openai_client():
    """Get or initialize the OpenAI client"""
    global _client
    
    if _client is not None:
        return _client
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    
    if not openai_api_key:
        print("Warning: OPENAI_API_KEY environment variable is not set")
        return None
    
    try:
        # Build client with minimal parameters to avoid proxy issues
        client_kwargs = {
            "api_key": openai_api_key,
        }
        
        if openai_base_url:
            client_kwargs["base_url"] = openai_base_url
        
        # Initialize with httpx client to avoid proxy configuration issues
        import httpx
        http_client = httpx.Client()
        client_kwargs["http_client"] = http_client
        
        _client = OpenAI(**client_kwargs)
        print(f"✓ OpenAI client initialized successfully")
        print(f"  Base URL: {openai_base_url or 'default'}")
        print(f"  API Key: {openai_api_key[:20]}...")
        return _client
    except Exception as e:
        print(f"✗ Warning: OpenAI client initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_fallback_image_url(item_name):
    """
    Generate fallback image URL using Unsplash API when image generation fails.
    Returns a high-quality food image based on the item name.
    """
    try:
        unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        
        if not unsplash_key:
            # Use public Unsplash URL without API key (limited to 50/hour)
            search_query = quote(item_name.split()[0])  # Use first word
            return f"https://source.unsplash.com/400x400/?{search_query},food"
        
        # With API key for better reliability and more requests
        search_query = quote(item_name)
        return f"https://api.unsplash.com/photos/random?query={search_query}&w=400&h=400&client_id={unsplash_key}"
    except Exception as e:
        print(f"Fallback image URL generation failed: {e}")
        # Return a generic food placeholder
        return "https://via.placeholder.com/400x400?text=Food+Image"

def generate_meal_image(prompt):
    """
    Generate image for a meal item.
    Tries OpenAI image generation first, falls back to Unsplash if that fails.
    """
    try:
        client = get_openai_client()
        if not client or not prompt:
            # No client available, use fallback
            return get_fallback_image_url(prompt or "Food")
        
        image_model = os.getenv("OPENAI_IMAGE_MODEL_NAME", "stabilityai/stable-diffusion-xl-base-1.0")
        
        response = client.images.generate(
            model=image_model,
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print(f"Image generation failed: {e}, using fallback URL")
        # Extract item name from prompt if possible
        item_name = prompt.split()[4] if len(prompt.split()) > 4 else "Food"
        return get_fallback_image_url(item_name)

def generate_item_image_prompt(item_name, item_serving):
    """Generate a detailed image prompt for a meal item"""
    return f"Professional food photography of {item_name} ({item_serving}), appetizing presentation, studio lighting, on a plate, high quality, professional restaurant style"

def recommend_meals_for_user(profile, meal_type: str):
    
    # Get the client lazily
    client = get_openai_client()
    
    # Check if client is initialized
    if not client:
        return {
            "items": [],
            "image_url": "",
            "error": "OpenAI client not initialized. Please check API key configuration."
        }

    user_data = {
        "name": profile.name,
        "age": profile.age,
        "weight": profile.weight,
        "height_cm": profile.height_cm,
        "gender": profile.gender,
        "goal": profile.goal,                     # Weight Loss / Weight Gain / Muscle Gain
        "diet_preference": profile.diet_preference,   # Veg / Non-Veg / etc.
        "health_conditions": profile.health_conditions or [],
        "allergies": profile.allergies or [],
    }

    system_prompt = (
        "You are a nutritionist. For the given user, suggest suitable Indian food options "
        "for one meal (breakfast/lunch/snacks/dinner). "
        "Follow these rules:\n"
        "- Strongly respect diet_preference (Veg, Non-Veg, Vegan, Eggetarian, Keto/Low-Carb, High Protein).\n"
        "- STRICTLY avoid ALL allergens mentioned in allergies list.\n"
        "- Respect health_conditions (e.g. Diabetes -> avoid sugar, simple carbs).\n"
        "- Give foods that are realistic, commonly available.\n"
        "- Respond ONLY as JSON with a single object: "
        "{ 'items': [ { 'name', 'serving', 'calories', 'protein_g', 'carbs_g', 'fats_g', 'note' } ], "
        "'image_prompt': 'A detailed visual description of the main dish recommended, suitable for generating an image' }.\n"
        "- calories/macros can be approximate, but reasonable.\n"
        "- 8 to 10 items max."
    )

    user_prompt = {
        "meal_type": meal_type,
        "user": user_data,
    }

    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt)},
            ],
            temperature=0.5,
        )
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {
            "items": [],
            "image_url": "",
            "error": f"Failed to generate meal recommendations: {str(e)}"
        }

    raw = resp.choices[0].message.content

    try:
        data = json.loads(raw)
        items = data.get("items", [])
        image_prompt = data.get("image_prompt", "")
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        items = [{"name": raw, "serving": "", "calories": 0, "protein_g": 0, "carbs_g": 0, "fats_g": 0, "note": ""}]
        image_prompt = ""

    # Generate image if prompt is available
    image_url = generate_meal_image(image_prompt) if image_prompt else get_fallback_image_url("Food")

    # small safety: only keep 5–8 records, ensure required keys present
    # Generate individual image for each item
    cleaned = []
    for item in items[:8]:
        item_name = item.get("name", "")
        item_serving = item.get("serving", "")
        
        # Generate image prompt for this specific item
        item_image_prompt = generate_item_image_prompt(item_name, item_serving)
        item_image_url = generate_meal_image(item_image_prompt)
        
        # Ensure item_image_url is not empty (use fallback if needed)
        if not item_image_url:
            item_image_url = get_fallback_image_url(item_name)
        
        cleaned.append(
            {
                "name": item_name,
                "serving": item_serving,
                "calories": item.get("calories", 0),
                "protein_g": item.get("protein_g", 0),
                "carbs_g": item.get("carbs_g", 0),
                "fats_g": item.get("fats_g", 0),
                "note": item.get("note", ""),
                "image_url": item_image_url,
            }
        )

    return {
        "items": cleaned,
        "image_url": image_url
    }
