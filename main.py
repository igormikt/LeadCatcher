# -*- coding: utf-8 -*-
import sqlite3
import datetime
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

# === НАСТРОЙКИ ===
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "leads.db"
LOG_PATH = BASE_DIR / "events.log"

# === ЛОГИРОВАНИЕ ===
logger = logging.getLogger("LeadCatcher")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8', mode='a')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False

# === МОДЕЛЬ ДАННЫХ ===
class Lead(BaseModel):
    name: str = Field(..., min_length=1, description="Имя клиента")
    contact: str = Field(..., min_length=1, description="Телефон или email")
    source: str = Field(..., min_length=1, description="Источник заявки")
    comment: str = Field(default="", description="Комментарий")

# === БАЗА ДАННЫХ ===
def init_db():
    """Создаёт таблицу leads, если её нет."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            contact TEXT NOT NULL,
            source TEXT NOT NULL,
            comment TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

# === СОВРЕМЕННЫЙ LIFESPAN (вместо устаревшего on_event) ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запуск и остановка приложения."""
    init_db()
    logger.info("LeadCatcher запущен")
    yield
    logger.info("LeadCatcher остановлен")

# === ПРИЛОЖЕНИЕ ===
app = FastAPI(
    title="LeadCatcher",
    description="MVP-сервис приёма заявок",
    version="1.0.0",
    lifespan=lifespan
)

# === ENDPOINT: POST /lead ===
@app.post("/lead")
def create_lead(lead: Lead):
    """Принимает заявку, сохраняет в БД, пишет в лог."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        created_at = datetime.datetime.now().isoformat()
        cursor = conn.execute(
            "INSERT INTO leads (created_at, name, contact, source, comment) VALUES (?, ?, ?, ?, ?)",
            (created_at, lead.name, lead.contact, lead.source, lead.comment)
        )
        conn.commit()
        lead_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"New lead saved: {lead_id}")
        
        return {"status": "ok", "id": lead_id, "message": "Lead accepted"}
    
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

# === ОБРАБОТКА ОШИБОК ===
@app.exception_handler(RequestValidationError)
async def validation_handler(exc: RequestValidationError):
    """HTTP 400 при ошибках валидации."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(status_code=400, content={"detail": "Invalid data", "errors": exc.errors()})

@app.exception_handler(Exception)
async def generic_handler(exc: Exception):
    """HTTP 500 при внутренних ошибках."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal error"})

# === HEALTH CHECK ===
@app.get("/")
def health():
    """Проверка работоспособности."""
    return {"service": "LeadCatcher", "status": "running"}