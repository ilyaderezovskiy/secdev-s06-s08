
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_echo_should_escape_script_tags():
    """GWT: Отражённая XSS не исполняется для script тегов"""
    resp = client.get("/echo", params={"msg": "<script>alert(1)</script>"})
    
    # Проверяем что теги удалены, но текст остается
    assert "<script>" not in resp.text
    assert "&lt;script&gt;" not in resp.text
    assert "alert(1)" in resp.text  # Текстовое содержимое должно остаться
    assert resp.status_code == 200

def test_img_onerror_not_executed():
    """GWT: XSS через img onerror не исполняется"""
    malicious_img = '<img src="x" onerror="alert(\'XSS\')">'
    resp = client.get("/echo", params={"msg": malicious_img})
    
    # Проверяем что HTML теги удалены, но текст содержимого остается
    assert "<img" not in resp.text
    assert "onerror" not in resp.text
    assert 'src="x"' not in resp.text
    assert "alert('XSS')" in resp.text  # Текст внутри onerror должен остаться
    assert resp.status_code == 200

def test_xss_multiple_vectors_blocked():
    """GWT: Различные XSS векторы блокируются"""
    xss_vectors = [
        ('<svg onload=alert(1)>', 'alert(1)'),  # (вектор, ожидаемый_текст)
        ('<body onload=alert(1)>', 'alert(1)'),
        ('<iframe src=javascript:alert(1)>', 'alert(1)'),
        ('<a href="javascript:alert(1)">click me</a>', 'click me'),
    ]
    
    for vector, expected_text in xss_vectors:
        resp = client.get("/echo", params={"msg": vector})
        
        # Проверяем что HTML теги удалены
        assert "<" + vector.split("<")[1].split(">")[0] + ">" not in resp.text, f"HTML tag should be removed: {vector}"
        
        # Проверяем что текстовое содержимое остается
        assert expected_text in resp.text, f"Text content should remain: {vector}"
        assert resp.status_code == 200

def test_safe_content_preserved():
    """GWT: Безопасный контент сохраняется правильно"""
    safe_content = [
        "Hello World!",
        "Normal text with symbols: <3 & >0",
        "Email: user@example.com",
    ]
    
    for content in safe_content:
        resp = client.get("/echo", params={"msg": content})
        assert resp.status_code == 200
        # Безопасный контент должен отображаться как есть
        assert content in resp.text
