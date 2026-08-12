# Kisan Mitra - AI-Powered Agricultural Voice Assistant

A production-ready voice agent system for Indian farmers, providing real-time agricultural guidance, market information, and expert escalation management via phone calls.

## Overview

Kisan Mitra is a multilingual (Hindi/English) voice assistant that:
- **Provides agricultural guidance** through natural voice conversations
- **Queries live market prices** (mandi data) for crops
- **Offers weather forecasts** for crop planning
- **Escalates complex problems** to agricultural experts
- **Manages automatic callbacks** to farmers with adviser solutions
- **Tracks escalations** through a Discord management interface

### Key Features

✅ **Voice AI Pipeline**
- Speech-to-Text (Deepgram) → LLM (Google Gemini) → Text-to-Speech (Murf AI)
- Natural conversation with silence detection and turn management
- Latency tracking and performance monitoring

✅ **Agricultural Services**
- Real-time mandi (market) prices for 500+ commodities
- Open-Meteo weather API integration
- Farmer memory management (preferences, crops, location)

✅ **Escalation System**
- Expert escalation for complex crop problems
- Discord-based adviser management
- Automatic callback system via SIP
- Reference ID tracking (KM-YYYYMMDD-XXXX format)

✅ **Outbound Calling**
- Automatic SIP callbacks for weather alerts
- Expert resolution callbacks to farmers
- LiveKit + Asterisk/Linphone integration

## Project Structure

```
backend/
├── src/
│   ├── agent.py                 # Main voice agent session handler
│   ├── assistant.py             # LLM assistant with tool functions
│   ├── config.py                # Configuration management
│   ├── api/
│   │   ├── http_server.py      # FastAPI server for Discord/webhooks
│   │   ├── escalation_routes.py # Escalation API endpoints
│   │   └── weather_alert_route.py
│   ├── database/
│   │   ├── db.py               # SQLite database setup
│   │   ├── escalation_repository.py
│   │   └── farmer_repository.py
│   ├── services/
│   │   ├── discord_service.py   # Discord bot integration
│   │   ├── escalation_callback_service.py
│   │   ├── escalation_service.py
│   │   ├── weather_service.py
│   │   ├── mandi_service.py
│   │   └── outbound_weather_service.py
│   ├── tools/
│   │   ├── escalation_tools.py
│   │   └── farmer_memory.py
│   ├── prompts/
│   │   └── kisan_prompt.py      # System prompts
│   └── utils/
│       ├── response_processor.py
│       ├── latency_tracker.py
│       └── silence_handler.py
├── data/
│   └── kisan_mitra.db           # SQLite database
├── pyproject.toml               # Python dependencies
├── .env.local                   # Configuration (add your credentials)
└── run_agent.py                 # Standalone agent runner

frontend/
├── package.json
├── src/
│   ├── App.tsx
│   ├── components/
│   └── ...
└── .env.local

telephony/
├── docker-compose.yml           # Asterisk + SIP configuration
├── asterisk_config/
│   ├── extensions.conf
│   ├── sip.conf
│   └── rtp.conf
└── README.md
```

## Installation & Setup

### Prerequisites

- **Python 3.11+** (tested with 3.13)
- **Node.js 18+** (for frontend)
- **Docker & Docker Compose** (for SIP/Asterisk)
- **FFmpeg** (for audio processing)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt  # auto-generated from pyproject.toml

# Configure environment
cp .env.example .env.local
# Edit .env.local with your API keys
```

### 2. Required API Keys & Configuration

Get credentials from these services and add to `.env.local`:

```
# LiveKit (https://cloud.livekit.io)
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Murf TTS (https://murf.ai)
MURF_API_KEY=your_murf_key

# Deepgram STT (https://deepgram.com)
DEEPGRAM_API_KEY=your_deepgram_key

# Google Gemini LLM (https://aistudio.google.com)
GOOGLE_API_KEY=your_gemini_key

# Discord Bot (https://discord.com/developers)
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_GUILD_ID=your_guild_id
DISCORD_ESCALATION_CHANNEL_ID=your_escalation_channel_id
DISCORD_RESOLVED_CHANNEL_ID=your_resolved_channel_id
DISCORD_ADVISER_ROLE_ID=your_adviser_role_id

# SIP Trunk (LiveKit SIP)
LIVEKIT_SIP_TRUNK_ID=your_sip_trunk_id
LINPHONE_SIP_URI=your_sip_destination

# Internal API
ESCALATION_INTERNAL_API_TOKEN=generate_a_random_token
```

### 3. Start Services

**Terminal 1 - HTTP Server (Escalation Management):**
```bash
cd backend
python -m uvicorn src.api.http_server:app --host 0.0.0.0 --port 8080
```

**Terminal 2 - LiveKit Agent (Voice Processing):**
```bash
cd backend
python src/agent.py dev
```

**Terminal 3 - Frontend (Optional):**
```bash
cd frontend
npm install
npm run dev
```

**Terminal 4 - SIP/Asterisk (Optional - for callbacks):**
```bash
cd backend/telephony
docker-compose up -d
```

## API Endpoints

### Health Check
```bash
GET http://localhost:8080/health
```

### Discord Status
```bash
GET http://localhost:8080/api/discord/status
```

### Escalation Management
```bash
# Get open escalations (requires Authorization header)
GET /api/escalations/open
Authorization: Bearer {ESCALATION_INTERNAL_API_TOKEN}

# Get specific escalation
GET /api/escalations/{reference_id}
Authorization: Bearer {ESCALATION_INTERNAL_API_TOKEN}

# Resolve escalation
POST /api/escalations/{reference_id}/resolve
Authorization: Bearer {ESCALATION_INTERNAL_API_TOKEN}
Content-Type: application/json

{
  "human_answer": "आपकी फसल को पत्ती धब्बा रोग है...",
  "resolution_notes": "Resolved by adviser_name"
}
```

## Discord Integration

### Setup

1. **Create Discord Bot:**
   - Go to https://discord.com/developers/applications
   - Create new application
   - Go to Bot tab → Add Bot
   - Copy token to `DISCORD_BOT_TOKEN`

2. **Get Guild & Channel IDs:**
   - Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
   - Right-click guild/channel → Copy Server/Channel ID
   - Add to `.env.local`

3. **Create Adviser Role:**
   - Create a role in Discord
   - Copy role ID to `DISCORD_ADVISER_ROLE_ID`
   - Assign to advisers

### Using /resolve Command

1. Adviser joins the Discord server with Adviser role
2. When escalation appears in #escalations channel, adviser uses:
   ```
   /resolve KM-20260812-0001 आपकी फसल को पत्ती धब्बा रोग है। नीम का तेल छिड़कें।
   ```
3. System automatically:
   - Resolves the escalation
   - Places SIP callback to farmer
   - Sends result to #resolved channel

## Escalation Workflow

```
1. FARMER CALLS
   ↓
2. Agent creates escalation (reference_id assigned)
   ↓
3. Discord notification sent to #escalations channel
   ↓
4. Adviser uses /resolve command
   ↓
5. Escalation marked RESOLVED
   ↓
6. Automatic SIP callback placed to farmer
   ↓
7. Agent speaks adviser's answer to farmer
   ↓
8. Result posted to #resolved channel (when call completes)
```

## Environment Variables

### Core Services
| Variable | Description | Example |
|----------|-------------|---------|
| `LIVEKIT_URL` | LiveKit server URL | `wss://livekit.example.com` |
| `LIVEKIT_API_KEY` | LiveKit API key | `APIxxxxxxx` |
| `LIVEKIT_API_SECRET` | LiveKit API secret | `xxxxx` |

### AI/ML Services
| Variable | Description | Example |
|----------|-------------|---------|
| `MURF_API_KEY` | Murf TTS API key | `ap2_xxxxx` |
| `DEEPGRAM_API_KEY` | Deepgram STT key | `xxxxx` |
| `GOOGLE_API_KEY` | Google Gemini LLM key | `AQ.Ab8R...` |

### Discord
| Variable | Description |
|----------|-------------|
| `DISCORD_BOT_TOKEN` | Discord bot token |
| `DISCORD_GUILD_ID` | Server ID |
| `DISCORD_ESCALATION_CHANNEL_ID` | Escalation channel |
| `DISCORD_RESOLVED_CHANNEL_ID` | Resolved escalations channel |
| `DISCORD_ADVISER_ROLE_ID` | Adviser role ID |

### SIP & Calling
| Variable | Description |
|----------|-------------|
| `LIVEKIT_SIP_TRUNK_ID` | LiveKit SIP trunk ID |
| `LINPHONE_SIP_URI` | SIP destination URI |
| `OUTBOUND_CALL_ENABLED` | Enable outbound calls (true/false) |

## Architecture Decisions

### Multi-Process Design
- **Agent Process**: Handles LiveKit voice sessions
- **HTTP Server Process**: Manages Discord bot & escalation APIs
- **SIP/Asterisk Container**: Manages phone routing

This prevents one process from blocking others and allows independent scaling.

### Escalation Reference ID
- Format: `KM-YYYYMMDD-SEQUENCE-UUID_HASH`
- UUID-based suffix ensures global uniqueness
- Prevents duplicate callbacks on concurrent escalations

### Discord Command Sync
- Global sync via background thread (5 seconds after bot connects)
- Ensures `/resolve` command appears in Discord client
- Handles timing issues with guild-specific sync

### SIP Callback Architecture
- Uses LiveKit native SIP integration
- Asterisk acts as local SIP bridge
- Agent joins outbound room and speaks adviser's answer
- Automatic hangup after call completes

## Troubleshooting

### Bot not appearing in Discord
- Clear Discord client cache
- Restart Discord
- Verify bot token in `.env.local`

### `/resolve` command not working
- Check adviser role is assigned
- Verify `DISCORD_ADVISER_ROLE_ID` in env
- Run: `GET /api/discord/status` to check bot connection

### Calls not going through
- Verify SIP trunk ID
- Check Linphone URI format
- Ensure Asterisk container is running
- Check LiveKit SIP integration logs

### Agent not responding
- Verify API keys (Gemini, Deepgram, Murf)
- Check LiveKit connection
- Review latency tracking logs

## Performance Metrics

### Typical Response Times
- **Speech Recognition**: 1-2 seconds
- **LLM Processing**: 2-4 seconds
- **TTS Generation**: 3-5 seconds
- **Total TTFB (Time to First Audio)**: 6-11 seconds

### Database
- **Queries**: < 10ms (SQLite in-memory mode available)
- **Escalation Creation**: < 50ms
- **Callback Placement**: < 2 seconds

## Security

### API Authentication
- All escalation endpoints require `Authorization: Bearer {token}`
- Token configured in `ESCALATION_INTERNAL_API_TOKEN`
- Discord adviser actions checked against role membership

### Database
- SQLite with transactions for atomicity
- Foreign key constraints enabled
- Prepared statements for all queries

### Environment Variables
- Never commit `.env.local` (in `.gitignore`)
- API keys rotated per environment
- Internal token should be strong random string

## Deployment

### Local Testing
```bash
# Start all services
./start_app.sh  # or start_app.ps1 on Windows
```

### Production Deployment

1. **Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Environment Setup**
   - Use `.env.local` on server
   - Set all required API keys
   - Use strong `ESCALATION_INTERNAL_API_TOKEN`

3. **Reverse Proxy**
   ```nginx
   location /api/ {
       proxy_pass http://localhost:8080;
       proxy_set_header Authorization $http_authorization;
   }
   ```

4. **Monitoring**
   - Monitor LiveKit connection health
   - Track escalation response times
   - Monitor Discord bot reconnects
   - Check SIP call success rate

## Future Enhancements

- [ ] WhatsApp integration for text-based support
- [ ] Multi-language support (Punjabi, Gujarati, etc.)
- [ ] Adviser dashboard for call analytics
- [ ] Farmer satisfaction feedback
- [ ] Automatic escalation suggestion (ML-based)
- [ ] Weather alert customization
- [ ] Crop disease image recognition

## License

Licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
1. Check [TROUBLESHOOTING](#troubleshooting) section
2. Review error logs in terminal output
3. Check Discord status: `GET /api/discord/status`
4. Contact: support@kisan-mitra.com

## Authors

Developed for the Murf VoiceForBharat Challenge

---

**Status**: ✅ Production Ready (Day 7)

**Last Updated**: August 12, 2026

**Version**: 1.0.0
