# Backend — Kisan Mitra Voice Agent

The Python backend for Kisan Mitra agriculture assistant. It runs a real-time voice AI pipeline using [LiveKit Agents](https://docs.livekit.io/agents), connecting Murf Falcon TTS, Deepgram STT, Google Gemini, and agricultural data APIs into a conversational farming assistant.

## How It Works

```
User speaks → [Deepgram STT] → text → [Gemini LLM + Tools] → response → [Murf Falcon TTS] → audio → User hears
                                           ↓
                                    [Weather API]
                                    [Mandi API]
                                    [Farmer Memory DB]
```

LiveKit handles the real-time audio transport. The agent connects to LiveKit as a participant, listens for user speech, calls appropriate tools (weather, mandi prices, memory), and responds with synthesized Hindi/English audio.

## Setup

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env.local
```

Fill in your keys in `.env.local`:

| Variable | Where to get it |
|----------|-----------------|
| `LIVEKIT_URL` | [LiveKit Cloud](https://cloud.livekit.io/) → Settings |
| `LIVEKIT_API_KEY` | [LiveKit Cloud](https://cloud.livekit.io/) → Settings |
| `LIVEKIT_API_SECRET` | [LiveKit Cloud](https://cloud.livekit.io/) → Settings |
| `MURF_API_KEY` | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) |
| `DEEPGRAM_API_KEY` | [deepgram.com](https://console.deepgram.com/) |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) |
| `MANDI_API_KEY` | [data.gov.in](https://data.gov.in/user/register) (optional - uses demo data if not set) |

For LiveKit Cloud users, you can auto-populate LiveKit credentials:

```bash
lk cloud auth
lk app env -w -d .env.local
```

### 3. Download models

```bash
uv run python src/agent.py download-files
```

This downloads Silero VAD and the LiveKit turn detector models.

### 4. Run the agent

```bash
# Development mode (auto-reload)
uv run python src/agent.py dev

# Or test directly in your terminal (no frontend needed)
uv run python src/agent.py console

# Production
uv run python src/agent.py start
```

## Configuration

All configuration lives in the `src/` directory:
- `src/agent.py` - Agent entrypoint and pipeline setup
- `src/config.py` - Centralized configuration (voice, timeouts, agent name)
- `src/prompts/kisan_prompt.py` - System prompt and conversation flow
- `src/assistant.py` - Assistant class with function tools

### System Prompt

The system prompt is in `src/prompts/kisan_prompt.py`. It defines:
- Agent identity (Kisan Mitra - female agriculture assistant)
- Language handling (Hindi/English bilingual)
- Tool usage rules (weather, mandi prices, farmer memory)
- Consent protocol for saving farmer information
- Conversation flow and greeting logic
- Safety guardrails and escalation rules

The prompt is structured for voice conversations - no markdown, short sentences, natural speech patterns.

### Voice

Voice is configured in `src/config.py`:

```python
VOICE_NAME = "hi-IN-anisha"  # Natural female Hindi voice
VOICE_STYLE = "Conversation"
```

The current voice (`hi-IN-anisha`) is specifically chosen for natural Hindi pronunciation with feminine speech patterns.

Browse all voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### Function Tools

Kisan Mitra has 4 function tools exposed to the LLM:

1. **`lookup_farmer(user_id)`** - Check if farmer exists in database, retrieve their profile
2. **`save_farmer_memory(...)`** - Save farmer information (only after consent)
3. **`get_weather(latitude, longitude, language)`** - Real-time weather data from Open-Meteo
4. **`get_mandi_prices(commodity, state, district, language)`** - Live mandi prices from Indian Government API

These are defined in `src/assistant.py` as `@function_tool` decorated methods.

### STT (Speech-to-Text)

Default is Deepgram Nova-3. Change in the `AgentSession(stt=...)` call:

```python
stt=deepgram.STT(model="nova-3")
```

### LLM

Default is Google Gemini. To switch:

- **Gemini (default):** Set `GOOGLE_API_KEY` in `.env.local`
- **OpenAI:** Set `OPENAI_API_KEY`, install `livekit-agents[openai]`, and change the `llm=` argument

## Testing

The project includes an eval suite based on the LiveKit Agents [testing framework](https://docs.livekit.io/agents/build/testing/):

```bash
uv run pytest
```

Tests are in [`tests/test_agent.py`](tests/test_agent.py) and use LLM-as-judge evaluations to verify the agent behaves correctly (friendly greetings, grounding, refusing harmful requests).

To run tests in CI, you'll need to add `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` as repository secrets.

## Deployment

### Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:
- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY`
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

### Docker

A production-ready [Dockerfile](Dockerfile) is included:

```bash
docker build -t murf-voice-agent .
docker run --env-file .env.local murf-voice-agent
```

## Project Structure

```
backend/
├── src/
│   ├── agent.py                  # Agent entrypoint — pipeline setup
│   ├── assistant.py              # KisanMitraAssistant class with function tools
│   ├── config.py                 # Centralized configuration
│   ├── prompts/
│   │   ├── kisan_prompt.py       # System prompt and conversation logic
│   │   └── __init__.py
│   ├── services/
│   │   ├── weather_service.py    # Weather API integration (Open-Meteo)
│   │   ├── mandi_service.py      # Mandi prices API integration
│   │   └── __init__.py
│   ├── database/
│   │   ├── db.py                 # SQLite database connection
│   │   ├── farmer_repository.py  # Farmer CRUD operations
│   │   └── __init__.py
│   ├── tools/
│   │   ├── farmer_memory.py      # Farmer memory tools (lookup, save)
│   │   └── __init__.py
│   ├── utils/
│   │   ├── latency_tracker.py    # Pipeline latency measurement
│   │   ├── response_processor.py # Text cleanup for TTS
│   │   ├── silence_handler.py    # Inactivity monitoring
│   │   └── __init__.py
│   └── api/
│       └── clear_user_data.py    # API endpoint for data deletion
├── data/
│   └── kisan_mitra.db            # SQLite database (auto-created)
├── tests/
│   ├── test_agent.py             # Agent behavior tests
│   └── test_farmer_memory.py    # Memory system tests (22 tests)
├── .env.example                  # Environment variable template
├── .env.local                    # Your keys (gitignored)
├── pyproject.toml                # Python dependencies (uv)
├── Dockerfile                    # Production container
└── railway.toml                  # Railway deploy config
```

## Links

- [Murf Falcon TTS Docs](https://murf.ai/api/docs/text-to-speech/streaming)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Agents Docs](https://docs.livekit.io/agents)
- [Deepgram Nova-3 Docs](https://developers.deepgram.com)

## License

MIT — see [LICENSE](LICENSE).
