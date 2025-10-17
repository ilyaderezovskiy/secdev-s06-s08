
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_sql_injection_in_search_returns_200():
    """GWT: SQL injection в поиске не вызывает ошибок сервера"""
    sql_injection_payloads = [
        "test",  # нормальный запрос
        "test' OR '1'='1",  # SQL injection
        "test'; --",  # SQL comment
    ]
    
    for payload in sql_injection_payloads:
        resp = client.get("/search", params={"q": payload})
        # Главное - нет 500 ошибок
        assert resp.status_code != 500, f"Should not cause server errors: {payload}"
        assert resp.status_code in [200, 422]

def test_sql_injection_in_login_returns_401_or_422():
    """GWT: SQL injection в логине не обходит аутентификацию"""
    sql_injection_payloads = [
        {"username": "testuser", "password": "testpass"},  # нормальный
        {"username": "admin' --", "password": "anything"},  # SQL injection
        {"username": "admin", "password": "' OR '1'='1"},  # SQL injection
    ]
    
    for payload in sql_injection_payloads:
        resp = client.post("/login", json=payload)
        # Может быть 401 (не авторизован) или 422 (невалидные данные)
        assert resp.status_code in [401, 422], f"Should not bypass auth: {payload}"
