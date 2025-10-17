
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_echo_should_escape_script_tags():
    """GWT: Отражённая XSS не исполняется для script тегов"""
    # Given: Запуск /echo
    # When: GET /echo?msg=<script>alert(1)</script>
    resp = client.get("/echo", params={"msg": "<script>alert(1)</script>"})
    
    # Then: В ответе нет тега <script>, контент экранирован
    assert "<script>" not in resp.text, "Вывод должен экранировать потенциальную XSS-последовательность"
    assert "&lt;script&gt;" in resp.text, "Script теги должны быть экранированы как HTML entities"
    assert resp.status_code == 200

def test_img_onerror_not_executed():
    """GWT: XSS через img onerror не исполняется"""
    # Given: Запуск /echo
    # When: GET /echo?msg=<img onerror=alert(1)>
    malicious_img = '<img src="x" onerror="alert(\'XSS\')">'
    resp = client.get("/echo", params={"msg": malicious_img})
    
    # Then: В ответе нет тега img и onerror атрибута
    assert "<img" not in resp.text, "HTML теги должны быть удалены или экранированы"
    assert "onerror" not in resp.text, "JavaScript события должны быть удалены"
    assert resp.status_code == 200

def test_xss_multiple_vectors_blocked():
    """GWT: Различные XSS векторы блокируются"""
    # Given: Запуск /echo
    xss_vectors = [
        '<svg onload=alert(1)>',
        '<body onload=alert(1)>',
        '<iframe src=javascript:alert(1)>',
        '<a href="javascript:alert(1)">click</a>'
    ]
    
    for vector in xss_vectors:
        # When: GET /echo с различными XSS векторами
        resp = client.get("/echo", params={"msg": vector})
        
        # Then: Все векторы должны быть нейтрализованы
        assert "<" not in resp.text or "&lt;" in resp.text, f"Vector not escaped: {vector}"
        assert "javascript:" not in resp.text.lower(), f"JavaScript protocol not removed: {vector}"
        assert resp.status_code == 200
