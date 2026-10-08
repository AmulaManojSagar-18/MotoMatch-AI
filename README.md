# 🏍️ MotoMatch-AI

> **AI-powered motorcycle recommendation chatbot** — describe your riding needs in plain English and get a data-driven, hallucination-free bike recommendation from a curated 10-bike Indian catalog.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Browser)                           │
│                    React 19 Chat UI                             │
└────────────────────────┬────────────────────────────────────────┘
                         │  POST /chat   GET /bikes/{id}
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Conversational Agent                        │   │
│  │                                                         │   │
│  │  User Message                                           │   │
│  │       │                                                 │   │
│  │       ▼                                                 │   │
│  │  ┌──────────────┐    structured JSON                    │   │
│  │  │  LLM Analyze │ ──────────────────► PreferenceUpdate  │   │
│  │  │  (Qwen 2.5)  │    (intent + prefs)       │          │   │
│  │  └──────────────┘                            │          │   │
│  │                                              ▼          │   │
│  │  ┌─────────────┐   ┌────────────────────────────────┐  │   │
│  │  │  RAG Layer  │   │   Recommendation Engine        │  │   │
│  │  │             │   │   (Pure Python, NO LLM)        │  │   │
│  │  │ nomic-embed │   │                                │  │   │
│  │  │  + cosine   │   │  budget filter → normalize     │  │   │
│  │  │  similarity │   │  specs → factor scores →       │  │   │
│  │  │  + keyword  │   │  weight by prefs → rank        │  │   │
│  │  │  fallback   │   │                                │  │   │
│  │  └──────┬──────┘   └──────────────┬─────────────────┘  │   │
│  │         │ knowledge               │ best bike + score   │   │
│  │         │ queries                 ▼                     │   │
│  │         │          ┌──────────────────────┐            │   │
│  │         │          │  LLM Explain         │            │   │
│  │         │          │  (Qwen 2.5, grounded │            │   │
│  │         │          │   by facts only)     │            │   │
│  │         │          └──────────────────────┘            │   │
│  └─────────┼───────────────────────────────────────────────┘   │
│            │                                                    │
│  ┌─────────▼────────────────┐                                  │
│  │  PostgreSQL (Bike Catalog│                                  │
│  │  10 bikes, factual specs)│                                  │
│  └──────────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Ollama (Local)     │
              │  qwen2.5:7b         │
              │  nomic-embed-text   │
              └─────────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **Conversational Chat** | Multi-turn dialogue with memory — the agent accumulates your preferences across messages |
| 🎯 **Smart Recommendations** | Deterministic scoring engine using 6 weighted fit factors — zero hallucinations |
| 📚 **RAG Knowledge Q&A** | Ask spec questions ("What engine does the Hunter 350 have?") — answered from a vector-embedded catalog |
| 🏍️ **10-Bike Catalog** | Hero, Yamaha, Royal Enfield, Triumph, Honda, TVS, Bajaj — commuters to cafe racers |
| 💰 **Budget Filtering** | Strict budget filtering before scoring — never recommends what you can't afford |
| 🔒 **100% Local & Free** | Runs entirely on your machine via Ollama — no OpenAI API keys, no cloud costs |

---

## 🏍️ Bike Catalog

| # | Bike | Category | Price (approx.) |
|---|---|---|---|
| 1 | Hero Splendor+ | Commuter | ₹80,000 |
| 2 | Hero Xpulse 200 4V | Adventure | ₹1,50,000 |
| 3 | TVS Ronin 225 | Scrambler | ₹1,50,000 |
| 4 | Yamaha R15 V4 | Sport | ₹1,85,000 |
| 5 | Royal Enfield Hunter 350 | Roadster | ₹1,70,000 |
| 6 | Honda CB350 | Modern Classic | ₹2,00,000 |
| 7 | Triumph Speed 400 | Roadster | ₹2,40,000 |
| 8 | Bajaj Pulsar NS400Z | Sport Naked | ₹1,85,000 |
| 9 | Royal Enfield Guerrilla 450 | Roadster | ₹2,40,000 |
| 10 | Royal Enfield Continental GT 650 | Cafe Racer | ₹3,20,000 |

---

## 🛠️ Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — REST API framework
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) — ORM + PostgreSQL
- [Pydantic v2](https://docs.pydantic.dev/) — data validation & structured LLM outputs
- [Ollama](https://ollama.com/) — local LLM inference server
- Qwen 2.5 7B — natural-language understanding & explanations
- nomic-embed-text — vector embeddings for RAG
- Custom cosine-similarity in-memory vector store (no external vector DB)

**Frontend**
- [React 19](https://react.dev/) + TypeScript
- [Vite](https://vitejs.dev/) — build tool
- Plain CSS (no UI framework)

---

## 🚀 How to Run

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://www.python.org/) |
| PostgreSQL | 14+ | [postgresql.org](https://www.postgresql.org/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Ollama | latest | [ollama.com](https://ollama.com/) |

---

### Step 1 — Pull Ollama models

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

> This downloads ~5 GB total. Only needed once.

---

### Step 2 — PostgreSQL setup

Create the database (in psql or pgAdmin):

```sql
CREATE DATABASE motomatch;
```

---

### Step 3 — Backend setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set your PostgreSQL password
```

`.env` (key values to update):
```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/motomatch
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=nomic-embed-text
```

```bash
# 5. Seed the database (creates tables + inserts 10 bikes)
python scripts/seed.py

# 6. Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend is live at: **http://localhost:8000**
API docs (Swagger UI): **http://localhost:8000/docs**

---

### Step 4 — Frontend setup

Open a new terminal:

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start dev server
npm run dev
```

Frontend is live at: **http://localhost:5173**

---

## 📸 Output Screenshots

### Chat UI — Welcome Screen
```
┌─────────────────────────────────────────────────────────┐
│  🏍️ MotoMatch                              ● Online     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│         Find Your Perfect Ride                          │
│   Tell me your budget, riding style, and use case       │
│                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ City commute │ │ Weekend trips│ │ Budget under   │  │
│  │ under 1 lakh │ │ under 2 lakh │ │ 3 lakh touring │  │
│  └──────────────┘ └──────────────┘ └────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Ask me anything about bikes...              [→] │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Chat UI — Recommendation Response
```
┌─────────────────────────────────────────────────────────┐
│  You: I ride 40km daily on highways, budget 2.5 lakh,   │
│       mileage matters                                   │
├─────────────────────────────────────────────────────────┤
│  ★ Your recommended bike                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │  [bike image]   Honda CB350                       │ │
│  │                 Modern Classic                    │ │
│  │                 ₹2,00,000        87% match        │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │ 348cc  20.8PS  29.4Nm  35km/l  181kg  800mm  │ │ │
│  │  │ Dual ABS  5-speed manual                     │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │  Why this bike?                                   │ │
│  │  The CB350 is a strong match for your 40km        │ │
│  │  highway commute — its torquey 348cc engine and   │ │
│  │  15L tank give it excellent highway composure...  │ │
│  │                                                   │ │
│  │  ✓ fits_budget  ✓ good_mileage                   │ │
│  │  ✓ good_for_highway_and_weekend_trips             │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### FastAPI Swagger UI — `/docs`
```
POST  /chat          Send a message to the conversational agent
GET   /bikes         List all 10 bikes in the catalog
GET   /bikes/{id}    Get full specs for a single bike
POST  /recommend     Direct recommendation (single-shot, no chat)
```

---

## 🧠 How the Scoring Engine Works

```
User says: "I want a touring bike, budget ₹2 lakh, 40km daily highway"
                              │
                              ▼
              LLM extracts UserPreferences (JSON)
              {
                budget: 200000,
                daily_commute_km: 40,
                touring_usage: "high",
                mileage_priority: "medium"
              }
                              │
                              ▼
              Budget filter: keeps bikes ≤ ₹2,00,000
                              │
                              ▼
              Min-max normalize all specs across candidates
              (power, displacement, mileage, weight, clearance...)
                              │
                              ▼
              Compute 6 factor scores per bike:
              ┌──────────────────────────────────────────────┐
              │  city      = (lightness + low_seat + mileage) / 3    │
              │  touring   = (fuel + power + displacement + weight) / 4 │
              │  adventure = (clearance×2 + displacement) / 3        │
              │  comfort   = (displacement×2 + weight + low_seat) / 4 │
              │  mileage   = mileage (raw)                            │
              │  performance = (power + displacement) / 2            │
              └──────────────────────────────────────────────┘
                              │
                              ▼
              Apply preference weights:
              low=0.0  medium=1.0  high=2.0
              + daily commute ≥30km → mileage+1.0, comfort+0.5
                              │
                              ▼
              score = Σ(factor × weight) / total_weight × 100
                              │
                              ▼
              Rank all candidates → pick highest score
              → LLM writes grounded explanation from facts only
```

---

## 📁 Project Structure

```
MotoMatch/
├── backend/
│   ├── app/
│   │   ├── agent/          # Conversational agent, tools, prompts, memory
│   │   ├── ai/             # LLM provider abstraction (Ollama), preference extractor
│   │   ├── api/            # FastAPI routes (chat, bikes, recommend)
│   │   ├── core/           # Config (env settings)
│   │   ├── data/           # Bike catalog (source of truth)
│   │   ├── db/             # SQLAlchemy session + base
│   │   ├── models/         # ORM models (Bike table)
│   │   ├── rag/            # Vector store, embeddings, retriever
│   │   ├── recommendation/ # Scoring engine + schemas
│   │   ├── repositories/   # DB access layer
│   │   ├── schemas/        # Pydantic API schemas
│   │   └── services/       # Business logic services
│   ├── scripts/
│   │   └── seed.py         # DB seeder (creates tables + inserts catalog)
│   ├── tests/              # 49 passing pytest tests
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   │   └── bikes/          # 10 bike PNG images
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/       # ChatWindow, ChatMessage, ChatInput
│   │   │   ├── common/     # TypingIndicator
│   │   │   └── recommendation/ # RecommendationCard, BikeImage, BikeSpecs
│   │   ├── pages/          # ChatPage (main page)
│   │   ├── services/       # API client (fetch + AbortController)
│   │   ├── types/          # TypeScript interfaces
│   │   └── utils/          # formatPrice, humanizeFactor
│   ├── index.html
│   └── package.json
│
└── README.md
```

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v
```

Expected output: **49 passed**

Tests cover: scoring engine, preference extraction, RAG retrieval, agent routing, chat API, bikes API, recommendation API.

---

## 🔑 Key Design Decisions

**LLM extracts, engine decides** — The LLM never picks a bike. It only parses natural language into a typed `UserPreferences` object. The deterministic engine does the rest. Same preferences → same result, every time.

**Structured LLM outputs** — Agent analysis uses Ollama's JSON schema-constrained generation (`format_schema`), not just JSON mode. This dramatically reduces parse failures with smaller local models.

**RAG for knowledge, not for selection** — Vector embeddings and retrieval are used only for factual Q&A ("What's the seat height of the R15?"). They play zero role in which bike is recommended.

**Graceful offline fallback** — If Ollama is down: the RAG retriever falls back to keyword overlap search; the explanation step uses a template string. The app never crashes on an LLM failure.

---

## 📄 License

MIT
