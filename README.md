# ADHD Executive Function Ecosystem

A premium AI-powered ADHD executive-function ecosystem with emotionally intelligent coaching, adaptive behavioral support, specialized AI agents, and a modern, calming Next.js frontend.

## Architecture

```
┌─────────────────────────┐     ┌──────────────────────────┐
│   Next.js Frontend      │     │   FastAPI Backend        │
│   (Vercel)              │     │   (Render/Railway)       │
│                         │     │                          │
│  ┌─────────────────┐    │     │  ┌──────────────────┐   │
│  │  Pages:          │    │     │  │  /api/auth       │   │
│  │  • Landing      │────┼─────┼─▶│  /api/chat       │   │
│  │  • Dashboard    │    │     │  │  /api/scores     │   │
│  │  • Chat         │    │     │  │  /api/analytics  │   │
│  │  • Focus Mode   │    │     │  │  /api/agents     │   │
│  │  • Tasks        │    │     │  │  /api/memory     │   │
│  │  • Analytics    │    │     │  │  /api/settings   │   │
│  │  • Mood Track   │    │     │  └──────────────────┘   │
│  │  • Agents       │    │     │                          │
│  │  • Settings     │    │     │  ┌──────────────────┐   │
│  └─────────────────┘    │     │  │  AI Agents       │   │
│                         │     │  │  • Productivity  │   │
│  ┌─────────────────┐    │     │  │  • Task Breakdown│   │
│  │  State (Zustand)  │    │     │  │  • Focus Opt.   │   │
│  │  • User Store    │    │     │  │  • Mood/Burnout │   │
│  │  • Chat Store    │    │     │  │  • Habit Builder │   │
│  │  • Timer Store   │    │     │  │  • Intervention  │   │
│  │  • Analytics Store│   │     │  └──────────────────┘   │
│  └─────────────────┘    │     │                          │
│                         │     │  ┌──────────────────┐   │
│  ┌─────────────────┐    │     │  │  ML Pipeline     │   │
│  │  UI Library      │    │     │  │  • ADHD Risk    │   │
│  │  • shadcn/ui    │    │     │  │  • Productivity  │   │
│  │  • Tailwind v4  │    │     │  │  • Mental Health │   │
│  │  • Framer Motion│    │     │  │  • Stress Detect │   │
│  │  • Recharts     │    │     │  └──────────────────┘   │
│  └─────────────────┘    │     │                          │
│                         │     │  ┌──────────────────┐   │
│  ┌─────────────────┐    │     │  │  Memory System   │   │
│  │  TanStack Query  │    │     │  │  • ChromaDB     │   │
│  │  (Data Fetching) │    │     │  │  • User Profiles │   │
│  └─────────────────┘    │     │  │  • Session Mem   │   │
└─────────────────────────┘     │  └──────────────────┘   │
                                │                          │
                                │  ┌──────────────────┐   │
                                │  │  Database        │   │
                                │  │  • PostgreSQL    │   │
                                │  │  • SQLite (dev)  │   │
                                │  └──────────────────┘   │
                                └──────────────────────────┘
```

## Tech Stack

### Frontend
- **Framework:** Next.js 16+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4 + glassmorphism design
- **Animation:** Framer Motion
- **State:** Zustand
- **UI:** shadcn/ui + Radix UI primitives
- **Charts:** Recharts + Chart.js
- **Data Fetching:** TanStack Query
- **Forms:** React Hook Form + Zod validation

### Backend
- **API:** FastAPI + Uvicorn
- **ML Models:** Scikit-Learn, CatBoost
- **Database:** SQLite (dev) / PostgreSQL (production)
- **Memory:** ChromaDB (lightweight semantic retrieval)
- **AI:** Groq API (primary inference)

## Features

### Core Pages
| Page | Route | Description |
|------|-------|-------------|
| **Landing** | `/` | Startup-quality hero, feature showcase, testimonials |
| **Dashboard** | `/dashboard` | Wellness scores, streaks, focus timer, quick insights |
| **Chat** | `/chat` | Premium AI chat with streaming, voice, task cards |
| **Focus Mode** | `/focus` | Immersive fullscreen Pomodoro with ambient gradients |
| **Tasks** | `/tasks` | AI task breakdown, "Start Tiny" mode, overwhelm detection |
| **Analytics** | `/analytics` | Productivity trends, focus heatmaps, mood correlations |
| **Mood** | `/mood` | Emotional check-ins, habit streaks, dopamine rewards |
| **Agents** | `/agents` | 7 specialized AI agents with status and interventions |
| **Settings** | `/settings` | AI personality, themes, accessibility, language (12+) |

### ADHD-Specific UX
- **Overwhelm Mode** — Gentle, calming interface during high stress
- **Start Tiny Mode** — Everything breaks down into 2-minute microsteps
- **Time Blindness Helper** — Visual day progress bar
- **Emotional Check-ins** — Quick mood selection with trend tracking
- **Dopamine Celebrations** — Confetti, level ups, badge rewards
- **Focus Rescue** — Pomodoro timer with adaptive session recommendations

### AI Agent System
| Agent | Function |
|-------|----------|
| Productivity Coach | Task prioritization and energy-aware scheduling |
| Task Breakdown | Large tasks → manageable microsteps |
| Focus Optimization | Focus pattern analysis and session tuning |
| Mood & Burnout | Emotional state tracking and burnout prevention |
| Habit Builder | Habit formation with streak tracking |
| Intervention | Smart intervention timing and delivery |
| Accountability | Gentle check-ins and progress tracking |

### Memory System
- ChromaDB-powered semantic memory retrieval
- User profile persistence across sessions
- Behavioral pattern recognition
- Context-aware conversation history

## Getting Started

### Prerequisites
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
cd frontend-next && npm install
```

### Running the Backend
```bash
python src/api/main_api.py
# or
uvicorn src.api.main_api:app --host 0.0.0.0 --port 8000
```

### Running the Frontend
```bash
cd frontend-next && npm run dev
```

### Production Build
```bash
cd frontend-next && npm run build && npm start
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | User registration |
| `/auth/login` | POST | Authentication |
| `/auth/reset-password` | POST | Password reset |
| `/chat` | POST | AI chat with context |
| `/calculate_scores` | POST | Compute all ML scores |
| `/analytics` | POST | Behavioral insights |
| `/get_interventions` | POST | Personalized recommendations |
| `/agents/analyze` | POST | Orchestrate AI agents |
| `/task-paralysis/analyze` | POST | Task paralysis detection |
| `/memory/{username}` | GET/POST | Session memory CRUD |
| `/memory/{username}/search` | POST | Semantic memory search |
| `/settings/{username}` | GET/PUT | User settings |
| `/admin/health` | GET | Protected admin health check |

## Administrator Configuration

The system supports automatic administrative account bootstrapping on startup via environment variables.

### Environment Variables
To enable and configure the admin account, set the following environment variables:
- `ADMIN_USERNAME`: The username for the administrator account (e.g., `admin`).
- `ADMIN_PASSWORD`: A secure password for the admin account.

### Production Hardening
When the environment is running in production (detected via `ENVIRONMENT`, `ENV`, `RENDER`, or `NODE_ENV` settings):
1. **Fatal Startup**: The backend will fail to start if `ADMIN_USERNAME` or `ADMIN_PASSWORD` is missing.
2. **Complexity Enforcement**: The `ADMIN_PASSWORD` must meet the following strict complexity requirements, or startup will abort:
   - Minimum length of **12 characters**.
   - Contains at least one **uppercase letter** (`A-Z`).
   - Contains at least one **lowercase letter** (`a-z`).
   - Contains at least one **digit** (`0-9`).
   - Contains at least one **special character** (e.g., `!@#$%^&*()`).

In development mode, weak passwords or missing variables will only log a warning and skip bootstrapping to facilitate local testing.

### Administrative Credentials Rotation
To rotate administrative credentials securely:
1. Update the `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables in your deployment settings (e.g., on Render or in your `.env` file).
2. Restart/re-deploy the server.
3. On startup, the system will identify if the user already exists. If the username remains the same but the password changes, the existing user's password hash will **not** be automatically overwritten on database startup to prevent unintentional lockout. To reset/force update the password, you should manually update it via a db client or rotate to a new username, or delete the old admin user row from the `users` table so it gets recreated.

## Deployment

### Frontend (Vercel)
```bash
cd frontend-next
npm run build
# Deploy via Vercel CLI or GitHub integration
```

### Backend (Render/Railway)
```bash
# Use render.yaml config
# Or manually: uvicorn src.api.main_api:app --host 0.0.0.0
```

## Performance Targets
| Metric | Target |
|--------|--------|
| Initial load | <1.5s static + streaming |
| Chat streaming | <200ms first token |
| API response (cached) | <100ms |
| Memory usage | <400MB |
| Model inference | <50ms |

## Project Structure
```
├── frontend-next/        # Next.js 16 frontend
│   ├── src/app/          # Pages (App Router)
│   ├── src/components/   # UI + shared components
│   ├── src/stores/       # Zustand state
│   ├── src/lib/          # Types, utils, API client
│   └── src/services/     # API integration layer
├── src/                  # Backend
│   ├── api/             # FastAPI endpoints
│   ├── agents/          # AI agent system
│   ├── analytics/       # Behavioral intelligence
│   ├── memory/          # ChromaDB memory system
│   ├── task_paralysis/  # Task paralysis engine
│   ├── scoring/         # ML scoring engines
│   ├── ml_models/       # Model training & optimization
│   └── intervention/    # Intervention engine
├── models/               # Trained ML models (.pkl)
├── data/                 # Datasets
├── render.yaml           # Render deployment config
└── vercel.json           # Vercel deployment config
```
