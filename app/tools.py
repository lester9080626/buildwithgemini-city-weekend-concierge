import json
from google.adk.tools import ToolContext
from google.cloud import firestore


# Explicitly hardcoded GCP Project ID (project ID string, NOT project number)
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-77ad6185964c"

# Initialize Firestore client with explicit project ID
db = firestore.Client(project=FIRESTORE_PROJECT_ID)


def search_venues(city: str, category: str = None) -> str:
    """Search venues in the database for a given city and optional category.

    Args:
        city: The name of the city (e.g., 'San Francisco', 'New York').
        category: Optional category filter (e.g., 'dining', 'attraction', 'sight', 'hotel').

    Returns:
        JSON string containing matching venue records.
    """
    collection_ref = db.collection("venues")
    query_ref = collection_ref.where("city_lower", "==", city.strip().lower())
    if category:
        query_ref = query_ref.where("category_lower", "==", category.strip().lower())

    docs = query_ref.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        # Remove lowercase filter fields for cleaner response
        data.pop("city_lower", None)
        data.pop("category_lower", None)
        results.append(data)

    if not results:
        return f"No venues found in {city}" + (f" for category '{category}'" if category else "") + "."

    return json.dumps(results, indent=2)


def add_venue(
    name: str,
    city: str,
    category: str,
    description: str,
    price_tier: str = "$$",
    address: str = "",
    rating: float = 4.5,
) -> str:
    """Add a new venue or weekend spot to the database.

    Args:
        name: Name of the venue or spot.
        city: City where the venue is located.
        category: Category (e.g., 'dining', 'attraction', 'sight', 'hotel').
        description: Brief description of the venue.
        price_tier: Price rating (e.g., '$', '$$', '$$$').
        address: Physical address or general location.
        rating: Star rating out of 5.0 (default 4.5).

    Returns:
        Confirmation message with the new venue ID.
    """
    collection_ref = db.collection("venues")
    doc_ref = collection_ref.document()
    venue_data = {
        "name": name,
        "city": city,
        "city_lower": city.strip().lower(),
        "category": category,
        "category_lower": category.strip().lower(),
        "description": description,
        "price_tier": price_tier,
        "address": address,
        "rating": rating,
    }
    doc_ref.set(venue_data)
    return f"Successfully added venue '{name}' with ID '{doc_ref.id}' in {city}."


def generate_destination_preview(
    name: str,
    city: str,
    category: str = "Attraction",
    description: str = "",
    rating: float = 4.8,
) -> str:
    """Generate a getaway postcard preview image for a destination or venue and save it to Cloud Storage.

    Args:
        name: Name of the destination, spot, or venue.
        city: City or region of the spot.
        category: Category (e.g., 'Attraction', 'Dining', 'Hotel').
        description: Short description or tagline to show on the preview card.
        rating: Star rating (out of 5.0).

    Returns:
        Public image URL of the generated postcard preview.
    """
    import io
    import uuid
    from PIL import Image, ImageDraw
    from google.cloud import storage

    bucket_name = f"{FIRESTORE_PROJECT_ID}-city-weekend-concierge"

    width, height = 800, 500
    img = Image.new("RGB", (width, height), color="#1e1b4b")
    draw = ImageDraw.Draw(img)

    for y in range(height):
        r = int(30 + (y / height) * 40)
        g = int(27 + (y / height) * 20)
        b = int(75 + (y / height) * 60)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    draw.rounded_rectangle([30, 30, width - 30, height - 30], radius=20, outline="#6366f1", width=3)
    draw.rounded_rectangle([60, 60, 240, 95], radius=12, fill="#4f46e5")
    draw.text((80, 70), "WEEKEND GETAWAY", fill="white")

    draw.text((60, 130), name, fill="#f8fafc")
    draw.text((60, 180), f"{city} • {category.capitalize()} • {rating} ★", fill="#94a3b8")

    draw.rounded_rectangle([60, 240, width - 60, height - 60], radius=12, fill="#0f172a")
    desc_text = description if description else f"Featured {category.lower()} in {city} for weekend getaways."
    draw.text((80, 265), desc_text[:90], fill="#e2e8f0")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    image_bytes = buffer.getvalue()

    filename = f"preview_{uuid.uuid4().hex[:8]}.jpg"
    storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"previews/{filename}")
    blob.upload_from_string(image_bytes, content_type="image/jpeg")

    public_url = f"https://storage.googleapis.com/{bucket_name}/previews/{filename}"
    return f"Generated destination preview for '{name}'. Public image URL: {public_url}"


def calculate_trip_budget(
    lodging_cost: float,
    dining_cost: float,
    activities_cost: float,
    num_people: int = 1,
) -> str:
    """Calculate total getaway budget and per-person cost breakdown.

    Args:
        lodging_cost: Estimated total cost for accommodation/hotel.
        dining_cost: Estimated total cost for meals and dining.
        activities_cost: Estimated total cost for tickets and attractions.
        num_people: Number of travelers splitting the cost (default 1).

    Returns:
        JSON string with itemized breakdown and per-person totals.
    """
    num_people = max(1, num_people)
    subtotal = lodging_cost + dining_cost + activities_cost
    per_person = round(subtotal / num_people, 2)
    result = {
        "lodging_cost": lodging_cost,
        "dining_cost": dining_cost,
        "activities_cost": activities_cost,
        "total_budget": round(subtotal, 2),
        "num_travelers": num_people,
        "cost_per_person": per_person,
    }
    return json.dumps(result, indent=2)


def get_city_details(city_name: str) -> str:
    """Fetch real geographic, timezone, and demographic details for a city from the Open-Meteo Public API.

    Args:
        city_name: Name of the city to look up (e.g. 'San Francisco', 'New York', 'Paris').

    Returns:
        JSON string containing real coordinates, timezone, country, and population.
    """
    import urllib.parse
    import urllib.request

    encoded_name = urllib.parse.quote(city_name.strip())
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_name}&count=1"

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "CityWeekendConcierge/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results")
        if not results:
            return f"No location details found for '{city_name}'."

        first = results[0]
        summary = {
            "city": first.get("name"),
            "state_province": first.get("admin1"),
            "country": first.get("country"),
            "latitude": first.get("latitude"),
            "longitude": first.get("longitude"),
            "timezone": first.get("timezone"),
            "elevation_meters": first.get("elevation"),
            "population": first.get("population"),
        }
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error fetching city details from public API: {str(e)}"


def generate_destination_image(prompt: str, tool_context: ToolContext) -> str:
    """Generate an image for a destination or venue using gemini-3.1-flash-lite-image, save as an artifact, and upload to Cloud Storage.

    Args:
        prompt: Description of the getaway spot, venue, or landmark to generate.
        tool_context: ADK ToolContext for saving the artifact.

    Returns:
        Public https URL of the generated image in Cloud Storage.
    """
    import uuid
    from google import genai
    from google.cloud import storage
    from google.genai import types

    bucket_name = "qwiklabs-gcp-02-77ad6185964c-city-weekend-concierge"

    genai_client = genai.Client(
        vertexai=True, project=FIRESTORE_PROJECT_ID, location="global"
    )
    response = genai_client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        return "Error: No image bytes returned from gemini-3.1-flash-lite-image model."

    filename = f"getaway_{uuid.uuid4().hex[:8]}.jpg"

    # 1. Save artifact with tool_context so it appears in Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload same image bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"images/{filename}")
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/images/{filename}"
    return f"Generated destination image for '{prompt}'. Public image URL: {public_url}"


def generate_destination_video(
    prompt: str,
    title: str = "Destination Highlight",
    tool_context: ToolContext = None,
) -> str:
    """Generate a short video clip for a getaway spot, venue, or landmark using Google's Omni model (gemini-omni-flash-preview).

    Args:
        prompt: Detailed visual text prompt describing the scene (e.g. 'A 3-second cinematic drone video of Golden Gate Bridge at sunset').
        title: Name of the spot or venue associated with the video clip.
        tool_context: ADK ToolContext for saving the video artifact.

    Returns:
        Public HTTPS URL of the generated video in Cloud Storage.
    """
    import base64
    import uuid
    import requests
    import google.auth
    from google.auth.transport.requests import Request
    from google.cloud import storage
    from google.genai import types

    bucket_name = "qwiklabs-gcp-02-77ad6185964c-city-weekend-concierge"

    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    token = credentials.token

    url = f"https://aiplatform.googleapis.com/v1beta1/projects/{FIRESTORE_PROJECT_ID}/locations/global/interactions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gemini-omni-flash-preview",
        "input": [{"type": "text", "text": prompt}],
        "response_format": [
            {"type": "video", "aspect_ratio": "16:9", "duration": "3s"}
        ],
        "generation_config": {"video_config": {"task": "text_to_video"}},
    }

    res = requests.post(url, headers=headers, json=payload)
    if res.status_code != 200:
        return f"Failed to generate video via Omni API: {res.text}"

    steps = res.json().get("steps", [])
    video_bytes = None
    for step in steps:
        if step.get("type") == "model_output":
            for content in step.get("content", []):
                if content.get("type") == "video":
                    video_b64 = content.get("data")
                    if video_b64:
                        video_bytes = base64.b64decode(video_b64)
                        break

    if not video_bytes:
        return "Error: No video bytes returned from gemini-omni-flash-preview model."

    filename = f"video_{uuid.uuid4().hex[:8]}.mp4"

    # 1. Save artifact with tool_context so it appears in Playground Artifacts panel
    if tool_context:
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload same video bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"videos/{filename}")
    blob.upload_from_string(video_bytes, content_type="video/mp4")

    public_url = f"https://storage.googleapis.com/{bucket_name}/videos/{filename}"
    return f"Successfully generated destination video for '{title}'. Public video URL: {public_url}"





