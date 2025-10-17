
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED
from markupsafe import Markup
from typing import Optional
import re
import html
import sqlite3

from .models import LoginRequest
from .db import query, query_one

app = FastAPI(title="secdev-seed-s06-s08")
templates = Jinja2Templates(directory="app/templates")

def strip_html_tags_keep_text(text: str) -> str:
    """Удаляет HTML теги, но сохраняет текстовое содержимое и значения атрибутов.
    - Не трогает конструкции, которые не представляют собой тэги (например '<3').
    - Из тэгов сохраняет только значения атрибутов (например alert(1)), не имена атрибутов.
    - Очищает javascript:/vbscript: схемы из значений.
    """
    if not text:
        return ""

    # Регекс только для "настоящих" HTML-тегов: начинается с '<', затем optional '/', затем буква
    tag_re = re.compile(r'<\s*/?\s*[a-zA-Z][^>]*>', flags=re.DOTALL)

    # Регекс для извлечения значений атрибутов (в двойных/одинарных кавычках либо без):
    attr_re = re.compile(
        r'\b[a-zA-Z_:][-a-zA-Z0-9_:.]*'      # имя атрибута
        r'\s*=\s*'
        r'(?:'
        r'"([^"]*)"'
        r'|\'([^\']*)\''
        r'|([^>\s]+)'
        r')'
    )

    def replace_tag(match: re.Match) -> str:
        tag = match.group(0)
        values = []
        for m in attr_re.finditer(tag):
            # одна из групп содержит значение
            val = m.group(1) or m.group(2) or m.group(3) or ""
            if not val:
                continue
            val = html.unescape(val)
            val = re.sub(r'^\s*(javascript:|vbscript:)', '', val, flags=re.IGNORECASE)
            if val:
                values.append(val)
        return " " + " ".join(values) + " "
    without_tags = tag_re.sub(replace_tag, text)

    # Декодируем HTML сущности для остального текста
    decoded = html.unescape(without_tags)
    decoded = re.sub(r'javascript:', '[removed]', decoded, flags=re.IGNORECASE)
    decoded = re.sub(r'vbscript:', '[removed]', decoded, flags=re.IGNORECASE)
    decoded = re.sub(r'\bon[a-zA-Z0-9_-]*\s*=', '', decoded, flags=re.IGNORECASE)

    return decoded.strip()


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
def index(request: Request, msg: Optional[str] = None):
    clean_msg = strip_html_tags_keep_text(msg) if msg else "Hello!"
    return templates.TemplateResponse(
        "index.html", {"request": request, "message": Markup(clean_msg)})

@app.get("/echo", response_class=HTMLResponse)
def echo(request: Request, msg: Optional[str] = None):
    clean_msg = strip_html_tags_keep_text(msg) if msg else ""
    return templates.TemplateResponse(
        "index.html", {"request": request, "message": Markup(clean_msg)})

@app.get("/search")
def search(q: Optional[str] = Query(default=None, min_length=1, max_length=32)):
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
