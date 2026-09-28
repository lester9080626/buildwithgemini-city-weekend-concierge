# 🌇 City & Weekend Getaway Concierge

An agentic AI travel assistant built with the **Google Agent Development Kit (ADK)** and deployed on **Agent Engine**. It specializes in personalizing weekend getaway itineraries, discovering dining and venue options according to user preferences and dietary restrictions, calculating trip budgets, and generating visual destination previews (images and video).

![City Weekend Concierge Demo](demo.gif)

---

## 🌟 Architecture & Features

This codebase directly implements the following capabilities and Google Cloud integrations:

### 🧠 Cross-Session Long-Term Memory
- **Vertex AI Memory Bank (`VertexAiMemoryBankService`)**: Persists user travel history, favorite destinations, dietary restrictions (e.g., gluten-free, peanut allergy), and personal preferences across conversations.
- **`PreloadMemoryTool` & Callbacks**: Automatically loads prior session facts into context before model turns and writes session memories back to Memory Bank after turns complete.

### 🗄️ Database & Venue Management
- **Firestore (`google.cloud.firestore`)**: Queries curated venue records by city and category (`search_venues`) and allows users to add new getaway spots (`add_venue`).

### 🎨 AI Image & Video Generation
- **Vertex AI Image Model (`gemini-3.1-flash-lite-image`)**: Generates custom visual postcards for destinations (`generate_destination_image`), saves them as ADK session artifacts, and uploads raw bytes directly to Google Cloud Storage.
- **Vertex AI Omni Model (`gemini-omni-flash-preview`)**: Generates 3-second cinematic drone video clips for destinations (`generate_destination_video`) via the Vertex AI Interactions API in the `global` region, registering ADK artifacts and serving public HTTPS URLs.
- **Google Cloud Storage**: Stores generated JPEG images and MP4 videos in a public Cloud Storage bucket for direct inline rendering in chat interfaces.

### 🖥️ Structured UI (A2UI)
- **A2UI Schema Manager (v0.8 Basic Catalog)**: Emits structured display cards (`Card`, `Column`, `Row`, `Text`, `Image`) rendered natively in both `adk web` and the custom web frontend via `a2ui_callback`.

### 🧮 Secure Sandbox Code Execution
- **`AgentEngineSandboxCodeExecutor`**: Executes Python code in a secure sandbox to calculate accurate per-person budget breakdowns, accommodation costs, and activity expenses (`calculate_trip_budget`).

### 🌦️ Geolocation & Weather Tools
- **Open-Meteo & Nominatim Integration**: Provides live weather forecasts (`get_weather`) and geographic details including coordinates, elevation, and population (`get_city_details`).
- **Timezone Lookups**: Computes exact local time for destination cities using Python `zoneinfo` (`get_current_time`).

---

## 📋 Feature Status Matrix

| Feature | Implementation Status |
| :--- | :--- |
| Cross-session Memory (Memory Bank) | ✅ Implemented |
| Venue Database Lookups & Additions (Firestore) | ✅ Implemented |
| Image Generation (`gemini-3.1-flash-lite-image`) | ✅ Implemented |
| Video Generation (`gemini-omni-flash-preview`) | ✅ Implemented |
| Public Cloud Storage Assets (Images/Videos) | ✅ Implemented |
| A2UI Card Rendering | ✅ Implemented |
| Trip Budget Sandbox Calculator | ✅ Implemented |
| Geocoding & Live Weather | ✅ Implemented |
| FastAPI Proxy & Custom Chat UI | ✅ Implemented |
| Real-time Flight Ticket Price Engine | ⏳ *Planned, not yet implemented* |
| Interactive Restaurant Reservation Booking | ⏳ *Planned, not yet implemented* |
| Multi-user Shared Itinerary Collaboration | ⏳ *Planned, not yet implemented* |

---

## 🛠️ Local Setup & Running Instructions

### Prerequisites
- Python 3.11+
- `uv` package manager (`pip install uv`)
- `agents-cli` v1.1.0+ (`pip install google-agents-cli`)
- Google Cloud SDK authenticated (`gcloud auth login` and `gcloud auth application-default login`)

### 1. Running the Local ADK Playground
To launch the interactive ADK development UI (which includes the **Artifacts panel** for generated images and videos):

```bash
adk web --port 8000 .
```

Open `http://localhost:8000` in your web browser.

### 2. Running the Custom Web Frontend Locally
To start the FastAPI proxy and chat interface locally:

```bash
# Navigate to the frontend directory
cd frontend

# Install frontend dependencies
uv sync

# Set required environment variables
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<AGENT_ENGINE_ID>"
export AGENT_DIRECTORY="app"
export PORT="8080"

# Start the server
uv run python main.py
```

Open `http://localhost:8080` in your web browser.

### 3. Deploying to Agent Platform
To deploy or update the agent on Vertex AI Agent Engine:

```bash
agents-cli deploy --project <YOUR_GCP_PROJECT_ID> --no-confirm-project
```

### 4. Deploying Frontend to Cloud Run
To ship the chat UI to Cloud Run:

```bash
gcloud run deploy city-weekend-concierge-frontend \
  --source ./frontend \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="<YOUR_AGENT_ENGINE_ID>",AGENT_DIRECTORY="app"
```

---

## 📁 Repository Structure

```
.
├── app/
│   ├── agent.py            # ADK agent definition, model config, and tool registrations
│   ├── tools.py            # Tool implementations (Firestore, Storage, Omni, Memory)
│   ├── a2ui_utils.py       # A2UI callback and JSON response formatter
│   └── __init__.py
├── frontend/
│   ├── main.py             # FastAPI proxy connecting browser to agent via A2A
│   ├── pyproject.toml
│   └── static/
│       └── index.html      # Responsive chat interface with prompt chips & A2UI renderer
├── agents-cli-manifest.yaml # Deployment specification manifest
├── pyproject.toml          # Root dependencies (ADK, Vertex AI SDK, GenAI SDK)
├── demo.gif                # Looping demo recording
└── README.md
```
