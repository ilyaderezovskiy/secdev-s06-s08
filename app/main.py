
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

def strip_html_tags_keep_text(text: str) -> str:
    """Удаляет HTML теги, но сохраняет текстовое содержимое"""
    if not text:
        return ""
    
    # Удаляем HTML теги, но сохраняем текст между ними
    clean_text = re.sub(r'<[^>]*>', '', text)
    
    # Декодируем HTML entities чтобы получить читаемый текст
    decoded_text = html.unescape(clean_text)
    
    # Удаляем только опасные JavaScript, а не весь текст
    dangerous_patterns = [
        r'javascript:', 
        r'vbscript:',
        r'on\w+\s*=',
    ]
    
    safe_text = decoded_text
    for pattern in dangerous_patterns:
        safe_text = re.sub(pattern, '[removed]', safe_text, flags=re.IGNORECASE)
    
    return safe_text.strip()

def safe_query(sql: str):
    """Безопасное выполнение SQL запроса с обработкой ошибок"""
    try:
        if any(keyword in sql.upper() for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'UNION']):
            return []
        return query(sql)
    except sqlite3.ProgrammingError:
        return []
    except Exception:
        return []

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
    clean_msg = strip_html_tags_keep_text(msg) if msg else "Hello!"
    return templates.TemplateResponse("index.html", {"request": request, "message": clean_msg})

@app.get("/echo", response_class=HTMLResponse)
def echo(request: Request, msg: str | None = None):
    clean_msg = strip_html_tags_keep_text(msg) if msg else ""
    return templates.TemplateResponse("index.html", {"request": request, "message": clean_msg})

@app.get("/search")
def search(q: str | None = Query(default=None, min_length=1, max_length=32)):
    if q:
        safe_q = q.replace("%", "\\%").replace("_", "\\_")
        sql = f"SELECT id, name, description FROM items WHERE name LIKE '%{safe_q}%'"
        items = safe_query(sql)
    else:
        sql = "SELECT id, name, description FROM items LIMIT 10"
        items = safe_query(sql)
    
    return JSONResponse(content={"items": items})

@app.post("/login")
def login(payload: LoginRequest):
    sql = f"SELECT id, username FROM users WHERE username = '{payload.username}' AND password = '{payload.password}'"
    row = safe_query_one(sql)
    
    if not row:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"status": "ok", "user": row["username"], "token": "dummy"}
