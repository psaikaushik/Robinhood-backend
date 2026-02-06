# Interview IDE Platform - Implementation Plan

This document outlines the plan to build a browser-based interview IDE with Claude AI integration and a Chaos Engine for interviewers.

## Overview

**Goal**: Build a CoderPad/HackerRank-like interview platform with:
- Browser-based VS Code (code-server)
- Claude AI chat sidebar
- Interviewer-only "Chaos Engine" control panel
- Demo with Robinhood-backend repo

**Deployment**: Local Docker for demo purposes

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Compose                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Frontend (React)                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  │ │
│  │  │ code-server │  │ Claude Chat │  │ Interviewer Panel  │  │ │
│  │  │   iframe    │  │  Sidebar    │  │ (role=interviewer) │  │ │
│  │  └─────────────┘  └─────────────┘  └────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Backend (FastAPI)                         │ │
│  │  - Session management                                       │ │
│  │  - Role-based auth (interviewer/candidate)                  │ │
│  │  - Claude API proxy                                         │ │
│  │  - Chaos Engine API                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│          ┌───────────────────┼───────────────────┐              │
│          ▼                   ▼                   ▼              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐    │
│  │ code-server  │   │  Robinhood   │   │    PostgreSQL    │    │
│  │  container   │   │   Backend    │   │   (sessions)     │    │
│  └──────────────┘   └──────────────┘   └──────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Work Packages (For Agents)

### WP1: Project Setup & Docker Infrastructure
**Estimated complexity**: Medium
**Dependencies**: None

**Tasks**:
1. Create new repository `interview-ide`
2. Set up Docker Compose with services:
   - `frontend`: React app (port 3000)
   - `backend`: FastAPI session manager (port 8080)
   - `code-server`: VS Code in browser (port 8443)
   - `target-app`: Robinhood backend (port 8000)
   - `postgres`: Session storage

3. Create base Dockerfiles for each service

**Files to create**:
```
interview-ide/
├── docker-compose.yml
├── frontend/
│   └── Dockerfile
├── backend/
│   └── Dockerfile
├── code-server/
│   └── Dockerfile
└── README.md
```

**Acceptance criteria**:
- `docker-compose up` starts all services
- code-server accessible at localhost:8443
- Can open Robinhood-backend in code-server

---

### WP2: Backend - Session & Auth Service
**Estimated complexity**: Medium
**Dependencies**: WP1

**Tasks**:
1. Create FastAPI backend with:
   - `POST /sessions` - Create interview session (returns interviewer + candidate links)
   - `GET /sessions/{id}` - Get session info
   - `POST /sessions/{id}/join` - Join as role
   - `GET /sessions/{id}/role` - Get current user's role

2. Session model:
   ```python
   class Session:
       id: str  # UUID
       interviewer_token: str  # Secret token for interviewer
       candidate_token: str  # Secret token for candidate
       created_at: datetime
       repo_url: str  # Git repo to clone
       chaos_scenario: str | None  # Currently active chaos
   ```

3. Role-based access:
   - Interviewer link: `http://localhost:3000/session/{id}?token={interviewer_token}`
   - Candidate link: `http://localhost:3000/session/{id}?token={candidate_token}`
   - Same session, different permissions

**Files to create**:
```
backend/
├── main.py
├── models/
│   └── session.py
├── routers/
│   ├── sessions.py
│   └── chaos.py
├── services/
│   └── session_manager.py
└── requirements.txt
```

**Acceptance criteria**:
- Can create session via API
- Interviewer and candidate get different tokens
- Role correctly identified from token

---

### WP3: Chaos Engine - Admin API
**Estimated complexity**: Low-Medium
**Dependencies**: WP2, Robinhood backend modifications

**Tasks**:
1. Add admin endpoints to Robinhood backend:
   ```python
   # POST /admin/chaos/activate
   # Body: {"scenario": "chaos_data" | "chaos_stress" | "chaos_race"}

   # POST /admin/chaos/reset
   # Resets to clean state

   # GET /admin/chaos/status
   # Returns current chaos state
   ```

2. Implement runtime chaos injection:
   - `chaos_data`: UPDATE stocks SET price = -50 WHERE symbol = 'GOOGL', etc.
   - `chaos_stress`: INSERT 500 alerts for stresstest user
   - `chaos_race`: Set global flag `CHAOS_RACE_ENABLED = True` (adds delays)

3. Add chaos router to interview-ide backend:
   ```python
   # POST /sessions/{id}/chaos
   # Body: {"scenario": "chaos_stress"}
   # Proxies to Robinhood /admin/chaos/activate
   ```

**Files to modify** (Robinhood-backend):
```
routers/admin.py  # NEW - admin endpoints
main.py           # Register admin router
services/chaos_runtime.py  # NEW - runtime chaos injection
```

**Files to create** (interview-ide):
```
backend/routers/chaos.py
```

**Acceptance criteria**:
- Interviewer can activate chaos via API
- Chaos takes effect without server restart
- Candidate's next request sees corrupted data / slow response / race condition

---

### WP4: Frontend - React Shell
**Estimated complexity**: Medium
**Dependencies**: WP1, WP2

**Tasks**:
1. Create React app with layout:
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │  Header: Session info, role badge                           │
   ├────────────────────────────────────┬────────────────────────┤
   │                                    │                        │
   │                                    │    Claude Chat         │
   │         code-server                │      Sidebar           │
   │           iframe                   │                        │
   │         (80% width)                │    (20% width)         │
   │                                    │                        │
   │                                    ├────────────────────────┤
   │                                    │  Chaos Engine Panel    │
   │                                    │  (interviewer only)    │
   └────────────────────────────────────┴────────────────────────┘
   ```

2. Components:
   - `<SessionProvider>` - Auth context with role
   - `<CodeServerFrame>` - iframe embedding code-server
   - `<ClaudeChat>` - Chat sidebar component
   - `<ChaosPanel>` - Interviewer-only chaos controls
   - `<RoleBadge>` - Shows "Interviewer" or "Candidate"

3. Routing:
   - `/` - Landing page (create session)
   - `/session/:id` - Main IDE view (role from token query param)

**Files to create**:
```
frontend/
├── src/
│   ├── App.tsx
│   ├── pages/
│   │   ├── Landing.tsx
│   │   └── Session.tsx
│   ├── components/
│   │   ├── CodeServerFrame.tsx
│   │   ├── ClaudeChat.tsx
│   │   ├── ChaosPanel.tsx
│   │   └── RoleBadge.tsx
│   ├── contexts/
│   │   └── SessionContext.tsx
│   └── api/
│       └── client.ts
├── package.json
└── vite.config.ts
```

**Acceptance criteria**:
- Landing page creates session and shows two links
- Session page shows code-server + chat sidebar
- Interviewer sees Chaos Panel, candidate does not

---

### WP5: Claude Chat Integration
**Estimated complexity**: Medium
**Dependencies**: WP4

**Tasks**:
1. Create Claude API proxy in backend:
   ```python
   # POST /sessions/{id}/chat
   # Body: {"message": "How do I fix this N+1 query?"}
   # Streams Claude response
   ```

2. Use Claude API with system prompt:
   ```
   You are a helpful coding assistant in a technical interview.
   The candidate is working on a Python/FastAPI project.
   Help them understand concepts but don't write complete solutions.
   ```

3. Frontend chat component:
   - Message input
   - Streaming response display
   - Chat history
   - Code syntax highlighting in responses

4. Context injection (optional enhancement):
   - Send current file content to Claude
   - "Ask about this file" button

**Files to create/modify**:
```
backend/
├── routers/chat.py
├── services/claude_service.py
└── config.py  # ANTHROPIC_API_KEY

frontend/src/components/
├── ClaudeChat.tsx
├── ChatMessage.tsx
└── ChatInput.tsx
```

**Acceptance criteria**:
- Candidate can ask questions in chat
- Claude responds with helpful hints
- Responses stream in real-time

---

### WP6: Chaos Panel UI
**Estimated complexity**: Low
**Dependencies**: WP3, WP4

**Tasks**:
1. Create ChaosPanel component:
   ```tsx
   <ChaosPanel>
     <h3>🔥 Chaos Engine</h3>
     <p>Current: {activeScenario || 'None'}</p>

     <button onClick={() => activateChaos('chaos_data')}>
       💾 Corrupt Data
     </button>

     <button onClick={() => activateChaos('chaos_stress')}>
       📈 High Volume (500 alerts)
     </button>

     <button onClick={() => activateChaos('chaos_race')}>
       🏃 Race Conditions
     </button>

     <button onClick={resetChaos}>
       🔄 Reset to Clean
     </button>
   </ChaosPanel>
   ```

2. Show confirmation dialog before activating
3. Show status indicator (active chaos scenario)
4. Only render for role === 'interviewer'

**Files to modify**:
```
frontend/src/components/ChaosPanel.tsx
frontend/src/pages/Session.tsx
```

**Acceptance criteria**:
- Chaos buttons only visible to interviewer
- Clicking activates chaos in Robinhood backend
- Status shows which chaos is active
- Reset returns to clean state

---

### WP7: code-server Configuration
**Estimated complexity**: Low
**Dependencies**: WP1

**Tasks**:
1. Configure code-server Docker image:
   - Pre-install Python extension
   - Pre-install Pylance
   - Set theme (Dark+)
   - Disable auth (handled by our frontend)

2. Mount Robinhood-backend repo into container
3. Configure terminal to auto-activate venv
4. Set up workspace settings

**Files to create**:
```
code-server/
├── Dockerfile
├── config.yaml
└── settings.json
```

**Acceptance criteria**:
- code-server loads with Python support
- Robinhood-backend visible in explorer
- Terminal has venv activated
- Can run `pytest` and `python main.py`

---

### WP8: Integration & Polish
**Estimated complexity**: Medium
**Dependencies**: All previous WPs

**Tasks**:
1. End-to-end testing:
   - Create session → get two links
   - Open interviewer link → see Chaos Panel
   - Open candidate link → no Chaos Panel
   - Activate chaos → candidate sees effect

2. Error handling:
   - Session not found
   - Invalid token
   - Chaos activation failed

3. UI polish:
   - Loading states
   - Error toasts
   - Responsive layout

4. Documentation:
   - README with setup instructions
   - Demo script

**Acceptance criteria**:
- Full demo flow works end-to-end
- Both roles have appropriate access
- Chaos Engine affects candidate's environment invisibly

---

## Quick Start (After Implementation)

```bash
# Clone the interview-ide repo
git clone <interview-ide-repo>
cd interview-ide

# Start all services
docker-compose up

# Open browser
# Go to http://localhost:3000

# Create a session
# Get interviewer link and candidate link
# Open both in separate browser windows

# As interviewer: Click "Chaos Engine" → "High Volume"
# As candidate: Run tests, observe slow performance
```

---

## Environment Variables

```env
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://user:pass@postgres:5432/sessions
CODE_SERVER_URL=http://code-server:8443
TARGET_APP_URL=http://target-app:8000

# frontend/.env
VITE_API_URL=http://localhost:8080
```

---

## Tech Stack Summary

| Component | Technology |
|-----------|------------|
| IDE | code-server (VS Code) |
| Frontend | React + TypeScript + Vite |
| Backend | FastAPI + Python |
| Database | PostgreSQL |
| AI | Claude API (Anthropic) |
| Container | Docker + Docker Compose |
| Target App | Robinhood-backend (FastAPI) |

---

## Agent Assignment Suggestion

| Work Package | Suggested Agent | Notes |
|--------------|-----------------|-------|
| WP1 | Bash agent | Docker/infra setup |
| WP2 | general-purpose | FastAPI backend |
| WP3 | general-purpose | Chaos API (both repos) |
| WP4 | general-purpose | React frontend |
| WP5 | general-purpose | Claude integration |
| WP6 | general-purpose | UI component |
| WP7 | Bash agent | Docker config |
| WP8 | general-purpose | Integration testing |

---

## References

- [code-server](https://github.com/coder/code-server) - VS Code in the browser
- [CoderPad](https://coderpad.io/) - Interview platform reference
- [HackerRank Interview](https://www.hackerrank.com/products/interview) - Interview platform reference
- [Claude API](https://docs.anthropic.com/claude/reference) - AI integration

