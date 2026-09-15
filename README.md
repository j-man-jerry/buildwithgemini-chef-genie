# ChefGenie 👨‍🍳✨

> **Your Personal AI Chef & Meal Planning Assistant built with Google ADK and Agent Platform**

ChefGenie is an autonomous AI chef and meal planning assistant that helps users discover personalized recipes, calculate macro nutrition, store favorite dishes, explore herbal remedies, and generate high-resolution dish plating visualizations.

![ChefGenie Demo](./demo.gif)

---

## 🚀 Key Features

- **🧠 Cross-Session Long-Term Memory**: Remembers your dietary restrictions, allergies, favorite cuisines, and household size across conversations using **Vertex AI Memory Bank**.
- **🎨 Rich A2UI Interface**: Delivers structured, responsive recipe cards, ingredient lists, and cooking steps rendered natively via **A2UI v0.8**.
- **🌿 Grounded Herbal RAG**: Answers questions about traditional plant remedies and herbal uses grounded on *Culpeper's Herbal* using a serverless **Vertex AI RAG Engine**.
- **📸 AI Dish Visualization**: Generates realistic plating visualizations using `gemini-3.1-flash-lite-image` in the `global` region and hosts public image URLs via **Google Cloud Storage**.
- **⚡ Safe Sandbox Code Execution**: Accurately scales recipe macros and portion sizes using **AgentEngineSandboxCodeExecutor** to execute Python code in a secure sandbox.
- **📚 Recipe Persistence**: Saves and searches your favorite recipes in a **Google Cloud Firestore** database.

---

## 🛠️ Google Cloud Tools & Architecture

ChefGenie leverages Google Cloud's Agent Platform ecosystem:

| Feature / Capability | Google Cloud / ADK Tool |
| -------------------- | ----------------------- |
| **Agent Runtime** | Vertex AI Agent Engine (Reasoning Engine) |
| **Long-Term Memory** | Vertex AI Memory Bank (`PreloadMemoryTool` + auto-memory callback) |
| **Document Retrieval (RAG)** | Vertex AI RAG Engine (`consult_herbal_corpus`) |
| **Database Storage** | Google Cloud Firestore (`save_recipe_firestore`, `search_recipes_firestore`) |
| **Media Hosting** | Google Cloud Storage Public Bucket (`chef-genie-media-*`) |
| **Image Generation** | `gemini-3.1-flash-lite-image` (Global Region) |
| **Code Execution** | `AgentEngineSandboxCodeExecutor` |
| **Rich UI Rendering** | A2UI (`A2uiSchemaManager` v0.8 + Basic Catalog) |
| **Web Frontend Proxy** | Cloud Run (`FastAPI` proxy talking over A2A protocol) |

### Architecture Flow

```
┌─────────────────────────┐         ┌───────────────────────────┐         ┌───────────────────────────────┐
│   Browser Chat UI       │  HTTP   │   FastAPI Proxy           │  A2A    │  Vertex AI Agent Runtime      │
│  (Custom HTML/Vanilla JS)│ ──────> │  (Cloud Run)              │ ──────> │  (ChefGenie ADK Agent)        │
└─────────────────────────┘         └───────────────────────────┘         └───────────────────────────────┘
                                                                                      │
                                                                   ┌──────────────────┴──────────────────┐
                                                                   ▼                                     ▼
                                                            ┌───────────────┐                   ┌────────────────┐
                                                            │ Memory Bank   │                   │  RAG Engine    │
                                                            │ Firestore     │                   │  Code Sandbox  │
                                                            │ Cloud Storage │                   │  Gemini Models │
                                                            └───────────────┘                   └────────────────┘
```

---

## 💻 Local Development

### 1. Prerequisites & Installation
Ensure you have Python 3.11+, `uv`, and `google-agents-cli` installed:
```bash
uv pip install -r frontend/requirements.txt
```

### 2. Run the Interactive Playground
Test ChefGenie locally in the ADK agent playground:
```bash
agents-cli playground
```

### 3. Run the Custom Frontend Locally
Start the FastAPI proxy and chat web UI on port `8080`:
```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/178057287160/locations/us-east1/reasoningEngines/5060788139862261760"
export AGENT_DIRECTORY="app"
uv run uvicorn frontend.main:app --port 8080
```
Open **`http://localhost:8080`** in your browser to chat!

---

## ☁️ Deployment

### Frontend (Cloud Run)
Deploy the frontend proxy to Cloud Run and grant the service account `roles/aiplatform.user`:
```bash
gcloud run deploy chef-genie-frontend \
  --source ./frontend \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/178057287160/locations/us-east1/reasoningEngines/5060788139862261760",AGENT_DIRECTORY="app"
```

---

## 📄 License
Licensed under the Apache License, Version 2.0.
