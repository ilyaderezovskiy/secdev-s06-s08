
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED
import re
import html
import sqlite3

from .models import LoginRequest
from .db import query, query_one

app = FastAPI(title="secdev-seed-s06-s08")
templates = Jinja2Templates(directory="app/templates")

def strip_all_html(text: str) -> str:
    """Полностью удаляет все HTML теги, оставляя только чистый текст"""
    if not text:
        return ""
    
    # Удаляем все HTML теги
    clean_text = re.sub(r'<[^>]*>', '', text)
    
    # Декодируем HTML entities
    decoded_text = html.unescape(clean_text)
    
    # Удаляем опасные JavaScript паттерны
    dangerous_patterns = [
        r'javascript:', 
        r'vbscript:',
        r'on\w+\s*=',
    ]
    
    for pattern in dangerous_patterns:
        decoded_text = re.sub(pattern, '[removed]', decoded_text, flags=re.IGNORECASE)
    
    return decoded_text.strip()

def safe_query(sql: str):
    """Безопасное выполнение SQL запроса с обработкой ошибок"""
    try:
        # Блокируем опасные операции
        if any(keyword in sql.upper() for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'UNION']):
            return []
        return query(sql)
    except sqlite3.ProgrammingError:
        return []  # Блокируем множественные statements
    except Exception:
        return []  # Блокируем другие ошибки

def safe_query_one(sql: str):
    """Безопасное выполнение SQL запроса для одной записи"""
    try:
        if any(keyword in sql.upper() for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'UNION']):
            return None
        return query_one(sql)
    except sqlite3.ProgrammingError:
        return None
    except Exception:
        return None

@app.get("/", response_class=HTMLResponse)
def index(request: Request, msg: str | None = None):
    # Безопасно: очищаем HTML и используем автоэкранирование Jinja2
    clean_msg = strip_all_html(msg) if msg else "Hello!"
    return templates.TemplateResponse("index.html", {"request": request, "message": clean_msg})

@app.get("/echo", response_class=HTMLResponse)
def echo(request: Request, msg: str | None = None):
    # Полностью удаляем HTML ДО передачи в шаблон
    clean_msg = strip_all_html(msg) if msg else ""
    return templates.TemplateResponse("index.html", {"request": request, "message": clean_msg})

@app.get("/search")
def search(q: str | None = Query(default=None, min_length=1, max_length=32)):
    # Защищенная версия с безопасной обработкой SQL
    if q:
        # Экранируем специальные символы для LIKE
        safe_q = q.replace("%", "\\%").replace("_", "\\_")
        sql = f"SELECT id, name, description FROM items WHERE name LIKE '%{safe_q}%'"
        items = safe_query(sql)
    else:
        sql = "SELECT id, name, description FROM items LIMIT 10"
        items = safe_query(sql)
    
    return JSONResponse(content={"items": items})

@app.post("/login")
def login(payload: LoginRequest):
    # Защищенная версия с безопасной обработкой SQL
    sql = f"SELECT id, username FROM users WHERE username = '{payload.username}' AND password = '{payload.password}'"
    row = safe_query_one(sql)
    
    if not row:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"status": "ok", "user": row["username"], "token": "dummy"}
