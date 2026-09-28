import sys
from google.cloud import firestore

# Explicitly hardcoded GCP Project ID (project ID string, NOT project number)
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-77ad6185964c"

SAMPLE_VENUES = [
    {
        "name": "Coit Tower & Telegraph Hill",
        "city": "San Francisco",
        "category": "attraction",
        "description": "Historic 210-foot tower offering panoramic views of San Francisco Bay and city skyline.",
        "price_tier": "$",
        "address": "1 Telegraph Hill Blvd, San Francisco, CA 94133",
        "rating": 4.7,
    },
    {
        "name": "Tartine Manufactory",
        "city": "San Francisco",
        "category": "dining",
        "description": "Acclaimed bakery & industrial café serving wood-fired breads, pastries, and seasonal California fare.",
        "price_tier": "$$",
        "address": "591 Alabama St, San Francisco, CA 94110",
        "rating": 4.6,
    },
    {
        "name": "High Line & Little Island Park",
        "city": "New York",
        "category": "attraction",
        "description": "Elevated linear park built on a former railway track with Hudson River views and public art.",
        "price_tier": "free",
        "address": "Gansevoort St to W 34th St, New York, NY 10011",
        "rating": 4.8,
    },
    {
        "name": "Katz's Delicatessen",
        "city": "New York",
        "category": "dining",
        "description": "Iconic Jewish deli operating since 1888, famous for legendary pastrami on rye sandwiches.",
        "price_tier": "$$",
        "address": "205 E Houston St, New York, NY 10002",
        "rating": 4.6,
    },
    {
        "name": "The Line Hotel SF",
        "city": "San Francisco",
        "category": "hotel",
        "description": "Modern boutique hotel in Theater District featuring rooftop cocktail lounge and city views.",
        "price_tier": "$$$",
        "address": "33 Turk St, San Francisco, CA 94102",
        "rating": 4.5,
    },
]


def seed():
    print(f"Connecting to Firestore project: {FIRESTORE_PROJECT_ID}...")
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    collection_ref = db.collection("venues")

    print(f"Seeding {len(SAMPLE_VENUES)} items into 'venues' collection...")
    for item in SAMPLE_VENUES:
        data = dict(item)
        data["city_lower"] = data["city"].strip().lower()
        data["category_lower"] = data["category"].strip().lower()

        doc_ref = collection_ref.document()
        doc_ref.set(data)
        print(f"  ✓ Added '{item['name']}' in {item['city']} (ID: {doc_ref.id})")

    print("\n✅ Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed()
