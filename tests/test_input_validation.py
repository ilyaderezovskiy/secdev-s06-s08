
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_username_too_long():
    """GWT: Слишком длинный логин отклоняется"""
    # Given: Ограничения модели (3..48 символов)
    # When: POST /login с username длиной > 48
    long_user = "u" * 49  # 49 символов > max_length=48
    payload = {"username": long_user, "password": "ValidPass123"}
    resp = client.post("/login", json=payload)
    
    # Then: 422 Unprocessable Entity
    assert resp.status_code == 422, "Слишком длинный username должен вызывать ошибку валидации"
    assert "max_length" in str(resp.json()).lower()

def test_login_username_invalid_chars():
    """GWT: Логин с запрещенными символами отклоняется"""
    # Given: Ограничения модели (только a-zA-Z0-9_.-)
    # When: POST /login с username содержащим запрещенные символы
    invalid_usernames = [
        "user@name",     # @ не разрешен
        "user name",     # пробел не разрешен
        "user$name",     # $ не разрешен
    ]
    
    for username in invalid_usernames:
        payload = {"username": username, "password": "ValidPass123"}
        resp = client.post("/login", json=payload)
        
        # Then: 422 Unprocessable Entity
        assert resp.status_code == 422, f"Username с запрещенными символами должен отклоняться: {username}"
        assert "pattern" in str(resp.json()).lower()

def test_search_query_too_long():
    """GWT: Слишком длинный поисковый запрос отклоняется"""
    # Given: Ограничения search (max_length=32)
    # When: GET /search с query длиной > 32
    long_query = "a" * 33  # 33 символа > max_length=32
    resp = client.get("/search", params={"q": long_query})
    
    # Then: 422 Unprocessable Entity
    assert resp.status_code == 422, "Слишком длинный поисковый запрос должен вызывать ошибку валидации"
    assert "max_length" in str(resp.json()).lower()

def test_search_query_too_short():
    """GWT: Слишком короткий поисковый запрос отклоняется"""
    # Given: Ограничения search (min_length=1)
    # When: GET /search с пустым query
    resp = client.get("/search", params={"q": ""})
    
    # Then: 422 Unprocessable Entity
    assert resp.status_code == 422, "Пустой поисковый запрос должен вызывать ошибку валидации"
    assert "min_length" in str(resp.json()).lower()
  
