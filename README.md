# Kisan Mitra — AI Agriculture Assistant for Indian Farmers

A production-ready voice AI agriculture assistant built on Murf Falcon TTS. Provides real-time farming guidance, weather information, and mandi (market) prices to Indian farmers in Hindi/English.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

> **Built For:** Indian farmers who need real-time agricultural guidance in their native language
>
> **Key Features:** Hindi/English voice support • Live weather data • Real-time mandi prices • Persistent farmer memory • Natural conversational flow

---

## What Makes Kisan Mitra Different

### Agriculture-Focused AI
- **Domain-specific knowledge** for Indian farming practices
- **Live data integration** - real weather and mandi prices, not guesses
- **Bilingual support** - seamless Hindi/English code-switching
- **Persistent memory** - remembers farmer details across conversations

### Technical Excellence
- **55ms TTS latency** with Murf Falcon - fastest production voice
- **Natural Hindi voice** with proper pronunciation
- **Robust error handling** - graceful fallbacks when APIs fail
- **Privacy-focused** - explicit consent before saving farmer data
- **SQLite persistence** - local farmer memory without external databases

### Real-World Tools
- **Weather API** - Live weather data from Open-Meteo (temperature, humidity, rain probability)
- **Mandi Price API** - Current market prices from Indian Government agricultural data
- **Farmer Memory** - Stores name, crops, district, land size with user consent
- **Smart Tool Chaining** - Automatically uses stored location for weather/price queries

---

## Architecture

```mermaid
flowchart LR
    A[🎙️ User speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[LLM]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit]
    E -->|stream| F[🔊 User hears]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#444441,stroke:#888780,color:#fff
```

---

## Quickstart

### Prerequisites

- **Python** 3.10+
- **[uv](https://docs.astral.sh/uv/)** - fast Python package manager
  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Node.js** 18+
- **pnpm** — fast Node package manager
  ```bash
  npm install -g pnpm
  ```
- A [LiveKit](https://cloud.livekit.io/) project (free tier available)

### Step 1: Clone the repo

```bash
git clone https://github.com/murf-ai/murf-livekit-starter.git
cd murf-livekit-starter
```

### Step 2: Set up environment variables

Create `.env.local` in both `backend/` and `frontend/` (copy from `.env.example` in each).

**Backend `.env.local`:**
```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Voice & STT
MURF_API_KEY=your_murf_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key

# LLM
GOOGLE_API_KEY=your_google_gemini_key

# Optional - Mandi Prices (if not provided, uses demo data)
MANDI_API_KEY=your_data_gov_in_api_key
```

**Frontend `.env.local`:**
```bash
# Must match backend LiveKit credentials
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Optional - for explicit agent dispatch
AGENT_NAME=my-agent
```

> **Important:** Keep your `.env.local` files secure and never commit them to version control. They are already in `.gitignore`.

| Variable | Where to get it | Required |
|----------|-----------------|----------|
| `LIVEKIT_URL` | LiveKit Cloud dashboard | Yes |
| `LIVEKIT_API_KEY` | LiveKit Cloud dashboard | Yes |
| `LIVEKIT_API_SECRET` | LiveKit Cloud dashboard | Yes |
| `MURF_API_KEY` | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) | Yes |
| `DEEPGRAM_API_KEY` | [deepgram.com](https://deepgram.com) | Yes |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) | Yes |
| `MANDI_API_KEY` | [data.gov.in](https://data.gov.in/user/register) (Indian Government Open Data) | Optional* |

> *Note: The Mandi Price API key is optional. If not provided, the agent will use fallback demo data for common crops (wheat, rice, onion). For production use with real-time market prices, register for a free API key at [data.gov.in](https://data.gov.in/user/register).

### Step 3: Install backend dependencies

```bash
cd backend
uv sync
uv run python src/agent.py download-files
```

### Step 4: Install frontend dependencies

```bash
cd frontend
pnpm install
```

### Step 5: Run it

**Option A - All-in-one (from repo root):**

```bash
# macOS/Linux
chmod +x start_app.sh
./start_app.sh

# Windows (PowerShell)
.\start_app.ps1
```

**Option B - Separate terminals:**

```bash
# Terminal 1 — LiveKit Server
livekit-server --dev

# Terminal 2 — Backend agent
cd backend && uv run python src/agent.py dev

# Terminal 3 — Frontend
cd frontend && pnpm dev
```

Then open **http://localhost:3000** in your browser.

You should now see the voice agent UI. Click **Start talking**, allow microphone access, and speak — the agent will respond with Murf Falcon TTS. Ensure your backend and (if using Option B) LiveKit server are running.

---

## Deploy

Want to deploy this beyond localhost? You'll need to deploy **two services**: the backend agent and the frontend. Both must use the same LiveKit project.

> This is a two-service app — the backend agent and the frontend UI deploy separately. You'll need both running and connected to the same LiveKit project.

### Backend (Python agent) — Deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:

- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

The backend runs as a long-lived Python process that connects to LiveKit as an agent. Railway handles this well.

### Frontend (Next.js) — Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/murf-ai/murf-livekit-starter&root-directory=frontend&env=LIVEKIT_URL,LIVEKIT_API_KEY,LIVEKIT_API_SECRET&project-name=murf-voice-agent&repository-name=murf-voice-agent)

Set these environment variables in Vercel:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `AGENT_NAME` (optional — for explicit agent dispatch)

The frontend is a standard Next.js app. Point it at the same LiveKit instance your backend agent is connected to.

### Connecting them

The frontend and backend don't call each other directly — they both connect to **LiveKit**, which handles the real-time audio transport.

1. Use the **same** `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` on both Railway and Vercel
2. Set `AGENT_NAME=my-agent` on Vercel — this matches the `agent_name="my-agent"` registered in `backend/src/agent.py`
3. Verify: Railway logs should show the agent connected to LiveKit. Open your Vercel URL, click **Start talking** — the agent should respond

If the agent doesn't connect, double-check that both services point to the same LiveKit project and that the backend is running (check Railway logs).

---

## Change the Use Case

The default system prompt makes this a **customer support agent**. You can change the agent’s behavior by editing the prompt.

**Where the prompt lives:** `backend/src/agent.py`- the `SYSTEM_PROMPT` constant (near the top of the file, after the imports). Change that string to change what your voice agent does.

### Example prompts (copy-paste)

**Customer Support (default):**

```
You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate.
```

**Language Tutor:**

```
You are a patient and encouraging language tutor helping the user practice conversational Spanish. Speak primarily in Spanish but switch to English to explain grammar or vocabulary when needed. Correct mistakes gently and suggest better phrasing. Keep conversations natural and fun.
```

**AI Receptionist:**

```
You are a professional receptionist for a medical clinic. Help callers schedule appointments, answer questions about office hours and services, and take messages for doctors. Be warm but efficient. Ask for the caller's name and reason for calling upfront.
```

See the Configuration section below for voice, STT, and LLM options.

---

## Configuration

### Murf voice

Edit the `tts=murf.TTS(...)` call in `backend/src/agent.py`. Set the `voice` argument to any Murf voice ID. Examples:

- `en-US-natalie` — US English (female)
- `en-UK-ruby` — UK English (female)
- `en-US-miles` — US English (male)
- `en-US-matthew` — US English (male, default in this starter)

Browse all voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT provider

STT is configured in `backend/src/agent.py` in the `AgentSession(stt=...)` call. The default is Deepgram (`deepgram.STT(model="nova-3")`). You can swap to another LiveKit-compatible STT plugin if needed.

### LLM (Gemini vs OpenAI)

- **Gemini (default):** Set `GOOGLE_API_KEY` and use `llm=google.LLM(model="gemini-2.5-flash")` in `agent.py`.
- **OpenAI:** Set `OPENAI_API_KEY`, add the OpenAI plugin, and use the corresponding `llm=openai.LLM(...)` in `agent.py`.

### Audio format

Murf Falcon and LiveKit handle audio format internally. For advanced options, see [Murf API docs](https://murf.ai/api/docs) and [LiveKit docs](https://docs.livekit.io).

---

## Project Structure

```
murf-livekit-starter/
├── backend/                 # Python voice agent (LiveKit Agents + Murf Falcon)
│   ├── src/
│   │   └── agent.py         # Agent entrypoint, pipeline (STT/LLM/TTS), system prompt
│   ├── tests/               # Agent tests
│   ├── .env.example         # Backend env template
│   ├── pyproject.toml       # Python deps (uv)
│   └── railway.toml         # Railway deploy config
├── frontend/                # Next.js UI for voice sessions
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   └── api/token/       # LiveKit token endpoint (dev)
│   ├── components/          # UI (agents-ui, app config, theme)
│   ├── app-config.ts        # Branding, title, button text, accent
│   ├── .env.example         # Frontend env template
│   └── package.json         # Node deps (pnpm)
├── start_app.sh             # Start LiveKit + backend + frontend (macOS/Linux)
├── start_app.ps1            # Start LiveKit + backend + frontend (Windows)
├── README.md                # This file
```

For deeper documentation on each part, see:

- [Backend Documentation](./backend/README.md) — agent pipeline, voice/LLM/STT configuration, testing, deployment
- [Frontend Documentation](./frontend/README.md) — UI customization, visualizers, theming, component architecture

---

## Links

- [Murf API Docs](https://murf.ai/api/docs)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Docs](https://docs.livekit.io)
- [Deepgram Docs](https://developers.deepgram.com)
- [Murf Falcon Benchmarks](https://murf.ai/falcon/benchmarks)
- [TTS Latency Benchmarker](https://github.com/sahilsgupta/tts-latency-benchmarker) — run your own p50/p95 tests across providers
- [Murf Discord](https://discord.gg/FbKAy96Sz7)
- [Murf Startup Incubator](https://murf.ai/api) — 50M free characters for startups

---

## Changelog & Implementation Details

### Day 7: Human-in-the-Loop Escalation System (IN PROGRESS)
**Changes:**
- 🚀 Complete escalation framework for serious farming issues
- 🚀 Human adviser integration via Discord
- 🚀 Automatic callback to farmer with adviser's answer
- 🚀 Permission-based escalation flow (explicit farmer consent required)
- 🚀 Escalation tracking and status management
- 🚀 Opt-out protection (respect farmer preferences)

**Features Implemented:**
1. **Escalation Request Creation**
   - Agent identifies serious crop problems or market data issues
   - Asks farmer permission before escalating
   - Creates escalation with reference ID (KM-YYYYMMDD-XXXX)
   - Escalation tracked in SQLite with full audit trail

2. **Escalation Reasons**
   - `SERIOUS_CROP_PROBLEM` - Severe crop damage, disease, widespread pest infestation
   - `MARKET_DATA_UNAVAILABLE` - Market price API failures or stale data
   - `UNCERTAIN_DIAGNOSIS` - Agent cannot confidently diagnose the issue
   - `OTHER` - General agricultural problems requiring expert help

3. **Discord Adviser Integration**
   - Open escalations displayed to authorized advisers
   - Modal form to submit resolution/answer
   - Role-based authorization (DISCORD_ADVISER_ROLE_ID)
   - Real-time status updates

4. **Automatic Callback System**
   - When adviser resolves escalation, automatic SIP call placed to farmer
   - Callback repeats original question, provides human answer
   - Uses existing outbound calling infrastructure
   - Respects farmer opt-out preferences
   - Retry logic with configurable max attempts

5. **Database Schema**
   - `escalations` table with full audit trail
   - Status tracking: OPEN → IN_PROGRESS → RESOLVED
   - Callback tracking: NOT_STARTED → QUEUED → CALLING → COMPLETED
   - Indexes on user_id, reference_id for fast queries

**Technical Architecture:**

```
Farmer Issue → Agent Tool: create_escalation()
    ↓
[Permission Check] → Farmer Must Say "हाँ" / "Yes"
    ↓
SQLite: INSERT into escalations (OPEN status)
    ↓
Discord Service: Send Notification to #escalations channel
    ↓
Adviser Reviews & Submits Answer via Modal
    ↓
Status: OPEN → RESOLVED + callback_status → QUEUED
    ↓
EscalationCallbackService: Trigger OutboundWeatherService
    ↓
SIP Call to Farmer's Phone
    ↓
Agent Repeats Question + Provides Human Answer
    ↓
Callback Complete: callback_status → COMPLETED
```

**Database Design:**
- Reference ID format: `KM-20260812-0042` (date + 4-digit sequence)
- Status: OPEN (awaiting adviser), IN_PROGRESS, RESOLVED
- Callback Status: NOT_STARTED, QUEUED, CALLING, CONNECTED, COMPLETED, NO_ANSWER, FAILED, SKIPPED_OPT_OUT
- Timestamps: created_at, updated_at, resolved_at, callback_timestamps
- Opt-out: Checks farmer.outbound_calls_enabled before placing call

**Files Created:**
- `backend/src/database/escalation_repository.py` - CRUD operations for escalations
- `backend/src/services/escalation_service.py` - Escalation determination logic
- `backend/src/services/escalation_callback_service.py` - Callback orchestration
- `backend/src/services/discord_service.py` - Discord bot integration (placeholder for discord.py)
- `backend/src/tools/escalation_tools.py` - Agent function tools
- `backend/src/api/escalation_routes.py` - HTTP API endpoints for Discord/advisers

**Files Modified:**
- `backend/src/database/db.py` - Added escalations table schema
- `backend/src/assistant.py` - Integrated escalation tools
- `backend/src/prompts/kisan_prompt.py` - Added escalation and permission flow instructions
- `backend/.env.example` - Added Discord and callback configuration

**Next Steps (To Complete):**
- [ ] Extend OutboundWeatherAlertService with `initiate_escalation_callback()` method
- [ ] Integrate escalation routes into FastAPI http_server
- [ ] Implement Discord bot with discord.py library
- [ ] Add authorization checks for adviser actions
- [ ] Implement idempotency protection for callbacks
- [ ] Add comprehensive logging with reference_id context
- [ ] Create unit tests for escalation flow
- [ ] End-to-end test: escalation → Discord → adviser resolution → callback

### Day 6: Outbound Weather Alerts & Production Fixes
**Changes:**
- ✅ Outbound weather alert calling system via SIP (LiveKit SIP Trunk → Linphone)
- ✅ Hindi speech normalization for natural Murf TTS pronunciation
- ✅ Farmer name personalization in outbound calls (database lookup)
- ✅ Do-not-call (opt-out) system with explicit opt-out handling
- ✅ Fixed late-join issue by separating greeting from weather content
- ✅ SQLite bug fix for Row object .get() method compatibility
- ✅ Frontend userId propagation through API chain for personalization

**Features Implemented:**
1. **Outbound Weather Alerts**
   - Calls triggered from weather alert button in UI
   - Message includes personalized greeting with farmer's actual name
   - Natural Hindi pronunciation: "70%" → "सत्तर प्रतिशत", "32°C" → "बत्तीस डिग्री"
   - Opt-out instructions in every call: "कॉल बंद कर दो"

2. **Hindi Speech Optimization**
   - `backend/src/utils/hindi_speech.py` module with comprehensive normalization
   - Converts numbers, temperatures, percentages to natural Hindi words
   - Weather condition mapping (English API responses → Hindi)
   - Removes technical markers for clean speech

3. **Farmer Personalization**
   - System looks up farmer by userId from database
   - Extracts name and language preference
   - Greeting: "नमस्ते {farmer_name} जी! किसान मित्र बोल रहा हूँ।"
   - Falls back to generic "नमस्ते!" if lookup fails

4. **Opt-Out System**
   - `outbound_calls_enabled` field in SQLite users table
   - `can_receive_outbound_calls()` check before placing calls
   - Opt-out detection in agent prompt (recognizes "कॉल बंद कर दो")
   - `save_farmer_memory(outbound_calls_enabled=False)` records preference

5. **Late-Join Fix**
   - Greeting spoken first (14 chars, ~400ms)
   - 1-second pause for call stabilization
   - Weather content spoken next
   - Users joining late still hear the full message

**Technical Details:**
- New files:
  - `backend/src/utils/hindi_speech.py` — Speech normalization
  - `backend/src/services/outbound_weather_service.py` — SIP call orchestration
  - `backend/src/api/http_server.py` — FastAPI HTTP endpoints
  - `backend/src/api/weather_alert_route.py` — Weather alert route handler
  - `frontend/components/kisan/WeatherAlertButton.tsx` — UI button component
  - `frontend/app/api/weather-alert/route.ts` — API bridge

- Modified files:
  - `backend/src/database/db.py` — Added `outbound_calls_enabled` column + migration
  - `backend/src/database/farmer_repository.py` — Fixed Row.get() bug, added opt-out methods
  - `backend/src/services/outbound_weather_service.py` — Full weather alert generation
  - `backend/src/agent.py` — Greeting separation, outbound call detection
  - `backend/src/assistant.py` — Outbound call mode detection
  - `backend/src/prompts/kisan_prompt.py` — Opt-out handling, outbound call instructions
  - `backend/src/tools/farmer_memory.py` — Pass through outbound_calls_enabled parameter

- Bug Fixes:
  - Fixed sqlite3.Row compatibility (replaced .get() with direct access + "in" check)
  - Fixed missing userId propagation through frontend → API → backend chain
  - Fixed speech normalization removing greeting (now detected and preserved)
  - Fixed late-join issue by splitting greeting/weather into separate TTS calls

**Testing:**
- Manual end-to-end: Make outbound call → Hear personalized greeting → Say "कॉल बंद कर दो" → Verify opt-out recorded
- Verified message generation includes greeting with farmer name
- Verified speech normalization preserves greeting and converts numbers correctly
- Verified late-join scenario (joining mid-call still hears weather content)

### Day 5: Mandi Price API Improvements
**Changes:**
- Enhanced error handling for mandi prices - gracefully handles 0 prices or missing data
- Agent now explicitly tells users when price data is unavailable
- Better fallback messages in Hindi/English
- Code cleanup and documentation updates

**Technical Details:**
- Updated `get_mandi_prices()` in `backend/src/assistant.py` to check for zero/null prices
- Returns user-friendly error messages instead of showing invalid data
- Preserves existing demo data fallback for common crops

### Day 4: Advanced Domain-Data Flow
**Changes:**
- Comprehensive farmer memory system with SQLite database
- Persistent storage of farmer profiles (name, crops, district, land, irrigation)
- Clear Data button in frontend UI
- Explicit consent flow before saving any farmer information
- Fixed silence handler to prevent premature disconnection
- Mobile-optimized UI with better touch targets and layout
- Frontend state management improvements

**Technical Details:**
- Database schema: `users` table + `farmer_profiles` table with foreign key
- `FarmerRepository` class for clean CRUD operations
- `FarmerMemoryTools` exposed as `@function_tool` for LLM access
- Added `delete_farmer()` method for data clearing
- Frontend `userIdGenerator` creates persistent localStorage-based user IDs
- Clear data API endpoint: `frontend/app/api/clear-data/route.ts`
- 22 comprehensive pytest tests for memory operations

### Day 3: Production Refactoring
**Changes:**
- Externalized system prompt to dedicated module (`backend/src/prompts/kisan_prompt.py`)
- Created centralized config (`backend/src/config.py`)
- Built clean `KisanMitraAssistant` class (`backend/src/assistant.py`)
- Added response post-processor to remove markdown/lists/emojis for natural voice output
- Structured project for scalability and maintainability

**Technical Details:**
- Prompt module exports `get_system_prompt()`, `get_greeting()`, `get_silence_reprompt()`
- Config module centralizes all constants (agent name, voice settings, timeouts)
- Response processor uses regex to clean text for TTS
- Modular architecture allows easy testing and updates

### Day 2: Agent Configuration & Voice
**Changes:**
- Comprehensive Kisan Mitra system prompt in Hindi/English
- Voice changed to `hi-IN-anisha` (natural female Hindi voice)
- Implemented inactivity monitoring (20s warning, 40s goodbye)
- Agent greets first automatically after connection
- Latency tracking for STT, LLM, TTS, and total response time
- Event-driven silence handler (no more polling)

**Technical Details:**
- `LatencyTracker` class measures each pipeline stage separately
- `ImprovedSilenceHandler` uses `agent_stopped_speaking` event
- Monitors silence only after agent speech, stops when user speaks
- Feminine pronouns and natural Hindi speech patterns in prompt

### Day 1: Live Data Integration
**Changes:**
- Weather API integration (Open-Meteo) for real-time data
- Mandi Prices API integration (Indian Government agricultural data)
- Function tools exposed to Gemini LLM
- Frontend Geolocation context for automatic location detection
- Tools return real-time verified data, never fabricate information

**Technical Details:**
- `WeatherService` class in `backend/src/services/weather_service.py`
- `MandiService` class in `backend/src/services/mandi_service.py`
- Both exposed as `@function_tool` methods in assistant
- Timeout handling (8-10s) with graceful fallbacks
- Demo data fallback for common crops when API unavailable
- System prompt updated with strict no-hallucination rules

---

## License

MIT
