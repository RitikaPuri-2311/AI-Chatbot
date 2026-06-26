from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, chat
from app.database import create_tables

app = FastAPI(title="AI Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await create_tables()

app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Chatbot API is running"}