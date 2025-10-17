
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_sql_injection_in_search_returns_200():
    """GWT: SQL injection в поиске не вызывает ошибок сервера"""
    sql_injection_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE items; --",
        "' UNION SELECT * FROM users --",
    ]
    
    for payload in sql_injection_payloads:
        resp = client.get("/search", params={"q": payload})
        # Главное - нет 500 ошибок, может быть 200 или 422
        assert resp.status_code != 500, f"SQL injection should not cause server errors: {payload}"

def test_sql_injection_in_login_returns_401_or_422():
    """GWT: SQL injection в логине не обходит аутентификацию"""
    sql_injection_payloads = [
        {"username": "admin' --", "password": "anything"},
        {"username": "admin", "password": "' OR '1'='1"},
        {"username": "' OR 1=1 --", "password": ""},
    ]
    
    for payload in sql_injection_payloads:
        resp = client.post("/login", json=payload)
        # Может быть 401 (не авторизован) или 422 (невалидные данные)
        assert resp.status_code in [401, 422], f"SQL injection should not bypass auth: {payload}"
