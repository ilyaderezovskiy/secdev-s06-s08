
# app/main.py
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED

from .models import LoginRequest
from .db import query, query_one

app = FastAPI(title="secdev-seed-s06-s08")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request, msg: str | None = None):
    # Теперь безопасно: используем автоэкранирование Jinja2
    return templates.TemplateResponse("index.html", {"request": request, "message": msg or "Hello!"})

@app.get("/echo", response_class=HTMLResponse)
def echo(request: Request, msg: str | None = None):
    return templates.TemplateResponse("index.html", {"request": request, "message": msg or ""})

# app/main.py
@app.get("/search")
def search(q: str | None = Query(default=None, min_length=1, max_length=32)):
    if q:
        sql = f"SELECT id, name, description FROM items WHERE name LIKE '%{q}%'"
        items = query(sql)  # Без второго параметра
    else:
        sql = "SELECT id, name, description FROM items LIMIT 10"
        items = query(sql)
    
    return JSONResponse(content={"items": items})

@app.post("/login")
def login(payload: LoginRequest):
    # Аналогично для login - используем текущую реализацию без параметров
    sql = f"SELECT id, username FROM users WHERE username = '{payload.username}' AND password = '{payload.password}'"
    row = query_one(sql)  # Без второго параметра
    
    if not row:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"status": "ok", "user": row["username"], "token": "dummy"}
