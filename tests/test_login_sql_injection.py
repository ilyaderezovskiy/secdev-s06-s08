
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_sql_injection_in_search_blocked():
    """GWT: SQL injection в поиске блокируется"""
    # Given: Защищенный search endpoint
    # When: GET /search с SQL injection payload
    sql_injection_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE items; --",
        "' UNION SELECT * FROM users --",
    ]
    
    for payload in sql_injection_payloads:
        resp = client.get("/search", params={"q": payload})
        
        # Then: Нет SQL ошибок (500), либо 200 либо 422
        assert resp.status_code != 500, f"SQL injection должен быть блокирован: {payload}"
        assert resp.status_code in [200, 422]

def test_sql_injection_in_login_blocked():
    """GWT: SQL injection в логине блокируется"""
    # Given: Защищенный login endpoint
    # When: POST /login с SQL injection payload
    sql_injection_payloads = [
        {"username": "admin' --", "password": "anything"},
        {"username": "admin", "password": "' OR '1'='1"},
        {"username": "' OR 1=1 --", "password": ""},
    ]
    
    for payload in sql_injection_payloads:
        resp = client.post("/login", json=payload)
        
        # Then: 401 Unauthorized (не обход авторизации)
        assert resp.status_code == 401, f"SQL injection в логине должен блокироваться: {payload}"
        assert "invalid credentials" in resp.json()["detail"].lower()
