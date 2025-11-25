import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from agent.state.session_memory import memory
# Import your existing AI agent function
from agent.graph.sports_agent_graph import build_graph
sports_agent_graph = build_graph()



# Initialize FastAPI app
app = FastAPI(title="Global Sports Intelligence Agent", version="1.0")

# --- CORS so frontend apps or local HTML can call this ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change this later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Logging setup ---
logger = logging.getLogger(__name__)

# --- In-memory chat memory ---
chat_memory = {}

# --- Pydantic model for request body ---
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = "default"

class SessionRequest(BaseModel):
    session_id: str

# Mount your web folder
app.mount("/web", StaticFiles(directory="web"), name="web")

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open("web/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(req: ChatRequest):
    user_message = req.message.strip()
    session_id = req.session_id or "default"

    if not user_message:
        return {"error": "Empty message"}

    logger.info(f"[CHAT] User ({session_id}): {user_message}")

    history = chat_memory.get(session_id, [])

    result = sports_agent_graph.invoke(
        {"user_input": user_message, "session_id": session_id},
        config={"configurable": {"thread_id": session_id}}
    )
    reply = result.get("output", str(result))

    history.append({"user": user_message, "agent": reply})
    chat_memory[session_id] = history[-5:]

    return {
        "reply": reply,
        "session_id": session_id,
        "memory": chat_memory[session_id],
    }
    
@app.post("/clear")
def clear_session(req: SessionRequest):
    session_id = req.session_id
    memory.clear(session_id)
    chat_memory[session_id] = []
    return {"status": "cleared", "session_id": session_id}

