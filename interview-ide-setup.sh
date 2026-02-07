#!/bin/bash
# Interview IDE - Complete Setup Script
# 
# USAGE:
# 1. Clone your empty repo: git clone https://github.com/psaikaushik/interview-ide.git
# 2. cd interview-ide
# 3. Save this entire file as setup.sh
# 4. Run: chmod +x setup.sh && ./setup.sh

set -e
echo "Creating Interview IDE project structure..."

# Create directories
mkdir -p backend/{routers,services,models}
mkdir -p frontend/src/{api,pages,contexts,components}
mkdir -p code-server target-app

echo "Creating root files..."

cat > '.gitignore' << 'EOF'
# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# Environment
.env
*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# Build outputs
dist/
build/

# Database
*.db
*.sqlite

# Logs
*.log

# Docker volumes
postgres-data/

# OS
.DS_Store
Thumbs.db
EOF

cat > '.env.example' << 'EOF'
# Anthropic API Key for Claude chat
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Optional: Set chaos scenario
# Original: chaos_data, chaos_stress, chaos_race
# Subtle: chaos_boundary, chaos_precision, chaos_inconsistent
SCENARIO=default
EOF

cat > 'docker-compose.yml' << 'EOF'
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8080
      - VITE_CODE_SERVER_URL=http://localhost:8443
    depends_on:
      - backend
    volumes:
      - ./frontend/src:/app/src

  backend:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://interview:interview123@postgres:5432/interview_ide
      - CODE_SERVER_URL=http://code-server:8443
      - TARGET_APP_URL=http://target-app:8000
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
      - target-app

  code-server:
    build: ./code-server
    ports:
      - "8443:8443"
    environment:
      - PASSWORD=
    volumes:
      - workspace:/home/coder/workspace
      - ./target-app:/home/coder/workspace/robinhood-backend

  target-app:
    build:
      context: ./target-app
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SCENARIO=${SCENARIO:-default}
    volumes:
      - target-app-db:/app/data

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=interview
      - POSTGRES_PASSWORD=interview123
      - POSTGRES_DB=interview_ide
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  workspace:
  target-app-db:
  postgres-data:
EOF

cat > 'README.md' << 'EOF'
# Interview IDE

A browser-based coding interview platform with Claude AI assistance and Chaos Engineering.

## Quick Start

1. Copy Robinhood-backend into target-app/
2. Create .env with your ANTHROPIC_API_KEY
3. Run: docker-compose up --build
4. Open http://localhost:3000

## Features

- Browser-based VS Code (code-server)
- Claude AI Chat sidebar
- Chaos Engine (interviewer only):
  - Corrupt Data - invalid stock prices
  - High Volume - 500 alerts for N+1 testing
  - Race Conditions - artificial delays
EOF

echo "Creating backend files..."

cat > 'backend/Dockerfile' << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
EOF

cat > 'backend/requirements.txt' << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.26.0
anthropic==0.18.1
pydantic==2.5.3
pydantic-settings==2.1.0
alembic==1.13.1
EOF

cat > 'backend/config.py' << 'EOF'
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = "postgresql://interview:interview123@localhost:5432/interview_ide"
    code_server_url: str = "http://localhost:8443"
    target_app_url: str = "http://localhost:8000"
    anthropic_api_key: str = ""
    secret_key: str = "interview-ide-secret-key-change-in-production"
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
EOF

cat > 'backend/main.py' << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import sessions, chat, chaos
from services.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Interview IDE API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(chaos.router, prefix="/chaos", tags=["Chaos Engine"])

@app.get("/")
async def root():
    return {"name": "Interview IDE API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
EOF

cat > 'backend/models/__init__.py' << 'EOF'
from models.session import Session
EOF

cat > 'backend/models/session.py' << 'EOF'
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
import uuid
from services.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interviewer_token = Column(String(64), unique=True, nullable=False)
    candidate_token = Column(String(64), unique=True, nullable=False)
    title = Column(String(255), default="Coding Interview")
    repo_url = Column(String(500), nullable=True)
    active_chaos = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    def to_dict(self, include_tokens: bool = False):
        data = {
            "id": self.id,
            "title": self.title,
            "repo_url": self.repo_url,
            "active_chaos": self.active_chaos,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }
        if include_tokens:
            data["interviewer_token"] = self.interviewer_token
            data["candidate_token"] = self.candidate_token
        return data
EOF

cat > 'backend/services/__init__.py' << 'EOF'
# Services package
EOF

cat > 'backend/services/database.py' << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

cat > 'backend/services/claude_service.py' << 'EOF'
from typing import List, Optional, AsyncGenerator
from anthropic import AsyncAnthropic
from config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are a helpful coding assistant in a technical interview environment.
The candidate is working on a Python/FastAPI backend project (a Robinhood clone).
Help them understand concepts and debug issues without giving complete solutions.
Keep responses concise and relevant to the coding task."""

class ClaudeService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def chat_stream(self, message: str, history: List[dict] = None, 
                          context: Optional[str] = None, role: str = "candidate") -> AsyncGenerator[str, None]:
        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})

        current_content = message
        if context:
            current_content = f"Current code context:\n```\n{context}\n```\n\nQuestion: {message}"
        messages.append({"role": "user", "content": current_content})

        system = SYSTEM_PROMPT
        if role == "interviewer":
            system += "\n\nNote: This user is the interviewer. You can provide more complete information."

        try:
            async with self.client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system,
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"Error: {str(e)}"
EOF

cat > 'backend/routers/__init__.py' << 'EOF'
# Routers package
EOF

cat > 'backend/routers/sessions.py' << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional
import secrets
from services.database import get_db
from models.session import Session

router = APIRouter()

class CreateSessionRequest(BaseModel):
    title: str = "Coding Interview"
    repo_url: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    title: str
    interviewer_url: str
    candidate_url: str
    created_at: str

class RoleResponse(BaseModel):
    role: str
    session_id: str
    title: str
    active_chaos: Optional[str]

@router.post("", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest, db: DBSession = Depends(get_db)):
    interviewer_token = secrets.token_urlsafe(32)
    candidate_token = secrets.token_urlsafe(32)

    session = Session(
        interviewer_token=interviewer_token,
        candidate_token=candidate_token,
        title=request.title,
        repo_url=request.repo_url
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    base_url = "http://localhost:3000"
    return SessionResponse(
        id=session.id,
        title=session.title,
        interviewer_url=f"{base_url}/session/{session.id}?token={interviewer_token}",
        candidate_url=f"{base_url}/session/{session.id}?token={candidate_token}",
        created_at=session.created_at.isoformat()
    )

@router.get("/{session_id}")
async def get_session(session_id: str, token: str = Query(...), db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if token == session.interviewer_token:
        role = "interviewer"
    elif token == session.candidate_token:
        role = "candidate"
    else:
        raise HTTPException(status_code=403, detail="Invalid token")

    return RoleResponse(role=role, session_id=session.id, title=session.title, active_chaos=session.active_chaos)
EOF

cat > 'backend/routers/chat.py' << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional, List
import json
from services.database import get_db
from services.claude_service import ClaudeService
from models.session import Session

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    context: Optional[str] = None

@router.post("/{session_id}")
async def chat(session_id: str, request: ChatRequest, token: str = Query(...), db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if token not in [session.interviewer_token, session.candidate_token]:
        raise HTTPException(status_code=403, detail="Invalid token")

    role = "interviewer" if token == session.interviewer_token else "candidate"
    claude = ClaudeService()

    async def generate():
        async for chunk in claude.chat_stream(
            message=request.message,
            history=request.history,
            context=request.context,
            role=role
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
EOF

cat > 'backend/routers/chaos.py' << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional
import httpx
from services.database import get_db
from models.session import Session
from config import get_settings

router = APIRouter()
settings = get_settings()

class ChaosRequest(BaseModel):
    scenario: str

class ChaosStatus(BaseModel):
    active: Optional[str]
    available: list[str]

AVAILABLE_SCENARIOS = [
    "chaos_data", "chaos_stress", "chaos_race",
    "chaos_boundary", "chaos_precision", "chaos_inconsistent"
]

@router.get("/{session_id}/status")
async def get_chaos_status(session_id: str, token: str = Query(...), db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if token != session.interviewer_token:
        raise HTTPException(status_code=403, detail="Interviewer access required")
    return ChaosStatus(active=session.active_chaos, available=AVAILABLE_SCENARIOS)

@router.post("/{session_id}/activate")
async def activate_chaos(session_id: str, request: ChaosRequest, token: str = Query(...), db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if token != session.interviewer_token:
        raise HTTPException(status_code=403, detail="Interviewer access required")
    if request.scenario not in AVAILABLE_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario. Available: {AVAILABLE_SCENARIOS}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.target_app_url}/admin/chaos/activate",
                                         json={"scenario": request.scenario}, timeout=30.0)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to activate chaos: {response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to target app: {str(e)}")

    session.active_chaos = request.scenario
    db.commit()
    return {"message": f"Chaos scenario '{request.scenario}' activated", "scenario": request.scenario}

@router.post("/{session_id}/reset")
async def reset_chaos(session_id: str, token: str = Query(...), db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if token != session.interviewer_token:
        raise HTTPException(status_code=403, detail="Interviewer access required")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.target_app_url}/admin/chaos/reset", timeout=30.0)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to reset chaos: {response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to target app: {str(e)}")

    session.active_chaos = None
    db.commit()
    return {"message": "Chaos reset to clean state"}
EOF

echo "Creating frontend files..."

cat > 'frontend/Dockerfile' << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
EOF

cat > 'frontend/package.json' << 'EOF'
{
  "name": "interview-ide-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.3",
    "react-markdown": "^9.0.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.12"
  }
}
EOF

cat > 'frontend/vite.config.ts' << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, host: '0.0.0.0' }
})
EOF

cat > 'frontend/tsconfig.json' << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF

cat > 'frontend/tsconfig.node.json' << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF

cat > 'frontend/index.html' << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Interview IDE</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

cat > 'frontend/src/main.tsx' << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
EOF

cat > 'frontend/src/App.tsx' << 'EOF'
import { Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Session from './pages/Session'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/session/:sessionId" element={<Session />} />
    </Routes>
  )
}

export default App
EOF

cat > 'frontend/src/index.css' << 'EOF'
:root {
  --bg-primary: #1e1e1e;
  --bg-secondary: #252526;
  --bg-tertiary: #2d2d2d;
  --text-primary: #cccccc;
  --text-secondary: #858585;
  --accent: #0078d4;
  --accent-hover: #1084d8;
  --success: #4caf50;
  --warning: #ff9800;
  --danger: #f44336;
  --border: #3c3c3c;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
}

#root { height: 100%; }

button {
  cursor: pointer;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  transition: background-color 0.2s;
}

button:disabled { opacity: 0.5; cursor: not-allowed; }

input, textarea {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
}

input:focus, textarea:focus { outline: none; border-color: var(--accent); }

.btn-primary { background-color: var(--accent); color: white; }
.btn-primary:hover:not(:disabled) { background-color: var(--accent-hover); }
.btn-danger { background-color: var(--danger); color: white; }
.btn-success { background-color: var(--success); color: white; }
EOF

cat > 'frontend/src/api/client.ts' << 'EOF'
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

export const api = {
  async createSession(title: string) {
    const response = await fetch(`${API_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    })
    if (!response.ok) throw new Error('Failed to create session')
    return response.json()
  },

  async getSession(sessionId: string, token: string) {
    const response = await fetch(`${API_URL}/sessions/${sessionId}?token=${encodeURIComponent(token)}`)
    if (!response.ok) throw new Error(response.status === 403 ? 'Invalid token' : 'Session not found')
    return response.json()
  },

  async getChaosStatus(sessionId: string, token: string) {
    const response = await fetch(`${API_URL}/chaos/${sessionId}/status?token=${encodeURIComponent(token)}`)
    if (!response.ok) throw new Error('Failed to get chaos status')
    return response.json()
  },

  async activateChaos(sessionId: string, token: string, scenario: string) {
    const response = await fetch(`${API_URL}/chaos/${sessionId}/activate?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario })
    })
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.detail || 'Failed to activate chaos')
    }
  },

  async resetChaos(sessionId: string, token: string) {
    const response = await fetch(`${API_URL}/chaos/${sessionId}/reset?token=${encodeURIComponent(token)}`, { method: 'POST' })
    if (!response.ok) throw new Error('Failed to reset chaos')
  },

  async sendChat(sessionId: string, token: string, message: string, history: any[] = [], onChunk: (chunk: string) => void) {
    const response = await fetch(`${API_URL}/chat/${sessionId}?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history })
    })
    if (!response.ok) throw new Error('Failed to send message')

    const reader = response.body?.getReader()
    if (!reader) return
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value)
      for (const line of text.split('\n')) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) onChunk(parsed.content)
          } catch {}
        }
      }
    }
  }
}
EOF

cat > 'frontend/src/contexts/SessionContext.tsx' << 'EOF'
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api } from '../api/client'

interface SessionContextType {
  sessionId: string
  token: string
  role: 'interviewer' | 'candidate' | null
  session: { title: string; active_chaos: string | null } | null
  loading: boolean
  error: string | null
  activeChaos: string | null
  refreshChaos: () => Promise<void>
}

const SessionContext = createContext<SessionContextType | null>(null)

export function SessionProvider({ sessionId, token, children }: { sessionId: string; token: string; children: ReactNode }) {
  const [role, setRole] = useState<'interviewer' | 'candidate' | null>(null)
  const [session, setSession] = useState<{ title: string; active_chaos: string | null } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeChaos, setActiveChaos] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      try {
        setLoading(true)
        const data = await api.getSession(sessionId, token)
        setRole(data.role)
        setSession({ title: data.title, active_chaos: data.active_chaos })
        setActiveChaos(data.active_chaos)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session')
      } finally {
        setLoading(false)
      }
    })()
  }, [sessionId, token])

  const refreshChaos = async () => {
    if (role !== 'interviewer') return
    try {
      const status = await api.getChaosStatus(sessionId, token)
      setActiveChaos(status.active)
    } catch {}
  }

  return (
    <SessionContext.Provider value={{ sessionId, token, role, session, loading, error, activeChaos, refreshChaos }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (!context) throw new Error('useSession must be used within SessionProvider')
  return context
}
EOF

cat > 'frontend/src/pages/Landing.tsx' << 'EOF'
import { useState } from 'react'
import { api } from '../api/client'

function Landing() {
  const [title, setTitle] = useState('Coding Interview')
  const [loading, setLoading] = useState(false)
  const [session, setSession] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const createSession = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.createSession(title)
      setSession(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session')
    } finally {
      setLoading(false)
    }
  }

  const copy = (text: string) => navigator.clipboard.writeText(text)

  return (
    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)' }}>
      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: 48, borderRadius: 12, maxWidth: 600, width: '90%' }}>
        <h1 style={{ fontSize: 32, marginBottom: 8, color: 'white' }}>Interview IDE</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 32 }}>Browser-based coding interviews with AI assistance</p>

        {!session ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Session Title</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} style={{ padding: 12, fontSize: 16 }} />
            </div>
            <button className="btn-primary" onClick={createSession} disabled={loading} style={{ padding: '14px 24px', fontSize: 16 }}>
              {loading ? 'Creating...' : 'Create Interview Session'}
            </button>
            {error && <p style={{ color: 'var(--danger)', fontSize: 14 }}>{error}</p>}
          </div>
        ) : (
          <div>
            <h2 style={{ color: 'var(--success)', marginBottom: 8 }}>Session Created!</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>ID: {session.id}</p>

            <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: 20, borderRadius: 8, marginBottom: 16 }}>
              <h3 style={{ fontSize: 16, marginBottom: 8 }}>Interviewer Link</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>Open this in your browser. You'll have access to the Chaos Engine.</p>
              <div style={{ display: 'flex', gap: 8 }}>
                <input value={session.interviewer_url} readOnly style={{ flex: 1, fontSize: 13 }} />
                <button className="btn-primary" onClick={() => copy(session.interviewer_url)}>Copy</button>
                <a href={session.interviewer_url} target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center' }}>Open</a>
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: 20, borderRadius: 8, marginBottom: 16 }}>
              <h3 style={{ fontSize: 16, marginBottom: 8 }}>Candidate Link</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>Share this with the candidate. They won't see the Chaos Engine.</p>
              <div style={{ display: 'flex', gap: 8 }}>
                <input value={session.candidate_url} readOnly style={{ flex: 1, fontSize: 13 }} />
                <button className="btn-primary" onClick={() => copy(session.candidate_url)}>Copy</button>
              </div>
            </div>

            <button onClick={() => setSession(null)} style={{ width: '100%', padding: 12, backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border)' }}>
              Create Another Session
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default Landing
EOF

cat > 'frontend/src/pages/Session.tsx' << 'EOF'
import { useParams, useSearchParams } from 'react-router-dom'
import { SessionProvider, useSession } from '../contexts/SessionContext'
import CodeServerFrame from '../components/CodeServerFrame'
import ClaudeChat from '../components/ClaudeChat'
import ChaosPanel from '../components/ChaosPanel'
import RoleBadge from '../components/RoleBadge'

function SessionContent() {
  const { role, session, loading, error } = useSession()

  if (loading) return <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading session...</div>
  if (error) return <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}><h2 style={{ color: 'var(--danger)' }}>Error</h2><p>{error}</p><a href="/" className="btn-primary">Back</a></div>

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ height: 48, backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h1 style={{ fontSize: 16, fontWeight: 600 }}>Interview IDE</h1>
          <span style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{session?.title}</span>
        </div>
        <RoleBadge role={role!} />
      </header>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{ flex: 1, minWidth: 0 }}><CodeServerFrame /></div>
        <div style={{ width: 350, backgroundColor: 'var(--bg-secondary)', borderLeft: '1px solid var(--border)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}><ClaudeChat /></div>
          {role === 'interviewer' && <div style={{ borderTop: '1px solid var(--border)', maxHeight: 280 }}><ChaosPanel /></div>}
        </div>
      </div>
    </div>
  )
}

function Session() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  if (!sessionId || !token) return <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}><h2 style={{ color: 'var(--danger)' }}>Invalid Link</h2><a href="/" className="btn-primary">Back</a></div>

  return <SessionProvider sessionId={sessionId} token={token}><SessionContent /></SessionProvider>
}

export default Session
EOF

cat > 'frontend/src/components/CodeServerFrame.tsx' << 'EOF'
const CODE_SERVER_URL = import.meta.env.VITE_CODE_SERVER_URL || 'http://localhost:8443'

function CodeServerFrame() {
  return (
    <div style={{ width: '100%', height: '100%' }}>
      <iframe src={CODE_SERVER_URL} title="VS Code" style={{ width: '100%', height: '100%', border: 'none' }} allow="clipboard-read; clipboard-write" />
    </div>
  )
}

export default CodeServerFrame
EOF

cat > 'frontend/src/components/RoleBadge.tsx' << 'EOF'
function RoleBadge({ role }: { role: 'interviewer' | 'candidate' }) {
  const isInterviewer = role === 'interviewer'
  return (
    <span style={{
      padding: '4px 12px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 500,
      textTransform: 'uppercase',
      backgroundColor: isInterviewer ? 'rgba(156, 39, 176, 0.2)' : 'rgba(33, 150, 243, 0.2)',
      color: isInterviewer ? '#ce93d8' : '#90caf9',
      border: `1px solid ${isInterviewer ? 'rgba(156, 39, 176, 0.3)' : 'rgba(33, 150, 243, 0.3)'}`
    }}>
      {isInterviewer ? 'Interviewer' : 'Candidate'}
    </span>
  )
}

export default RoleBadge
EOF

cat > 'frontend/src/components/ClaudeChat.tsx' << 'EOF'
import { useState, useRef, useEffect } from 'react'
import { useSession } from '../contexts/SessionContext'
import { api } from '../api/client'
import ReactMarkdown from 'react-markdown'

interface Message { role: 'user' | 'assistant'; content: string }

function ClaudeChat() {
  const { sessionId, token } = useSession()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }]
    setMessages(newMessages)
    setMessages([...newMessages, { role: 'assistant', content: '' }])

    try {
      let assistantContent = ''
      await api.sendChat(sessionId, token, userMessage, messages, (chunk) => {
        assistantContent += chunk
        setMessages([...newMessages, { role: 'assistant', content: assistantContent }])
      })
    } catch {
      setMessages([...newMessages, { role: 'assistant', content: 'Sorry, an error occurred. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 500 }}>
        <span style={{ width: 24, height: 24, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 'bold', color: 'white' }}>AI</span>
        <span>Claude Assistant</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '32px 16px' }}>
            <p>Ask me anything about the code!</p>
            <p style={{ fontSize: 13, marginTop: 8 }}>I can help with debugging or explaining concepts.</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} style={{ maxWidth: '90%', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{ backgroundColor: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-tertiary)', color: msg.role === 'user' ? 'white' : 'inherit', padding: '10px 14px', borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px' }}>
                {msg.role === 'assistant' ? <ReactMarkdown>{msg.content || '...'}</ReactMarkdown> : msg.content}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{ padding: 12, borderTop: '1px solid var(--border)', display: 'flex', gap: 8 }}>
        <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }}} placeholder="Ask a question..." disabled={loading} rows={2} style={{ flex: 1, resize: 'none', fontFamily: 'inherit' }} />
        <button className="btn-primary" onClick={sendMessage} disabled={loading || !input.trim()} style={{ alignSelf: 'flex-end', padding: '8px 16px' }}>{loading ? '...' : 'Send'}</button>
      </div>
    </div>
  )
}

export default ClaudeChat
EOF

cat > 'frontend/src/components/ChaosPanel.tsx' << 'EOF'
import { useState } from 'react'
import { useSession } from '../contexts/SessionContext'
import { api } from '../api/client'

const SCENARIOS = [
  // Original (obvious bugs)
  { id: 'chaos_data', name: 'Corrupt Data', icon: '💾', description: 'Negative/zero prices' },
  { id: 'chaos_stress', name: 'High Volume', icon: '📈', description: '500+ alerts (N+1 query)' },
  { id: 'chaos_race', name: 'Race Conditions', icon: '🏃', description: 'Timing delays' },
  // Subtle bugs (require investigation)
  { id: 'chaos_boundary', name: 'Boundary Cases', icon: '🎯', description: '>= vs > edge cases' },
  { id: 'chaos_precision', name: 'Float Precision', icon: '🔬', description: '0.1+0.2 != 0.3' },
  { id: 'chaos_inconsistent', name: 'Data Issues', icon: '🔀', description: 'Bad timestamps/duplicates' }
]

function ChaosPanel() {
  const { sessionId, token, activeChaos, refreshChaos } = useSession()
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const activate = async (id: string) => {
    if (loading) return
    setLoading(id)
    setError(null)
    try {
      await api.activateChaos(sessionId, token, id)
      await refreshChaos()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed')
    } finally {
      setLoading(null)
    }
  }

  const reset = async () => {
    if (loading) return
    setLoading('reset')
    setError(null)
    try {
      await api.resetChaos(sessionId, token)
      await refreshChaos()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 500 }}>
        <span>🔥</span>
        <span>Chaos Engine</span>
        {activeChaos && <span style={{ marginLeft: 'auto', backgroundColor: 'var(--danger)', color: 'white', padding: '2px 8px', borderRadius: 10, fontSize: 10, fontWeight: 'bold' }}>ACTIVE</span>}
      </div>

      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {activeChaos && <div style={{ backgroundColor: 'rgba(244, 67, 54, 0.1)', border: '1px solid rgba(244, 67, 54, 0.3)', padding: '8px 12px', borderRadius: 6, fontSize: 13 }}><strong>Active:</strong> {SCENARIOS.find(s => s.id === activeChaos)?.name}</div>}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {SCENARIOS.map((s) => (
            <button key={s.id} onClick={() => activate(s.id)} disabled={loading !== null}
              style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', backgroundColor: activeChaos === s.id ? 'rgba(244, 67, 54, 0.15)' : 'var(--bg-tertiary)', border: `1px solid ${activeChaos === s.id ? 'var(--danger)' : 'var(--border)'}`, borderRadius: 6, textAlign: 'left', cursor: loading ? 'not-allowed' : 'pointer' }}>
              <span style={{ fontSize: 18 }}>{s.icon}</span>
              <span style={{ flex: 1, fontSize: 13 }}>{s.name}</span>
              {loading === s.id && <span style={{ color: 'var(--text-secondary)' }}>...</span>}
            </button>
          ))}
        </div>

        {error && <p style={{ color: 'var(--danger)', fontSize: 12 }}>{error}</p>}

        <button onClick={reset} disabled={loading !== null || !activeChaos}
          style={{ backgroundColor: 'transparent', border: '1px solid var(--border)', color: 'var(--text-secondary)', padding: 8, fontSize: 13, cursor: loading || !activeChaos ? 'not-allowed' : 'pointer' }}>
          {loading === 'reset' ? 'Resetting...' : '🔄 Reset to Clean'}
        </button>
      </div>
    </div>
  )
}

export default ChaosPanel
EOF

echo "Creating code-server files..."

cat > 'code-server/Dockerfile' << 'EOF'
FROM codercom/code-server:4.20.0

USER root
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv git curl && rm -rf /var/lib/apt/lists/*
USER coder

RUN code-server --install-extension ms-python.python && code-server --install-extension ms-python.vscode-pylance
RUN mkdir -p /home/coder/workspace

COPY --chown=coder:coder settings.json /home/coder/.local/share/code-server/User/settings.json
COPY --chown=coder:coder config.yaml /home/coder/.config/code-server/config.yaml

WORKDIR /home/coder/workspace
EXPOSE 8443
CMD ["code-server", "--bind-addr", "0.0.0.0:8443", "/home/coder/workspace"]
EOF

cat > 'code-server/config.yaml' << 'EOF'
bind-addr: 0.0.0.0:8443
auth: none
cert: false
EOF

cat > 'code-server/settings.json' << 'EOF'
{
  "workbench.colorTheme": "Default Dark+",
  "editor.fontSize": 14,
  "editor.tabSize": 4,
  "editor.formatOnSave": true,
  "editor.minimap.enabled": false,
  "python.analysis.typeCheckingMode": "basic",
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "workbench.startupEditor": "none"
}
EOF

echo "Creating target-app files..."

cat > 'target-app/Dockerfile' << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

cat > 'target-app/.gitkeep' << 'EOF'
# Copy Robinhood-backend files here
EOF

echo ""
echo "=========================================="
echo "  Interview IDE setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Copy Robinhood-backend: cp -r ../Robinhood-backend/* target-app/"
echo "  2. Create .env: echo 'ANTHROPIC_API_KEY=your-key' > .env"
echo "  3. Run: docker-compose up --build"
echo "  4. Open: http://localhost:3000"
echo ""
