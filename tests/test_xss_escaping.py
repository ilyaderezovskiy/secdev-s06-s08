
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_echo_should_escape_script_tags():
    """GWT: Отражённая XSS не исполняется для script тегов"""
    resp = client.get("/echo", params={"msg": "<script>alert(1)</script>"})
    
    # Проверяем что теги полностью удалены, а не просто экранированы
    assert "<script>" not in resp.text
    assert "alert(1)" in resp.text  # Текст остается, но теги удалены
    assert resp.status_code == 200

def test_img_onerror_not_executed():
    """GWT: XSS через img onerror не исполняется"""
    malicious_img = '<img src="x" onerror="alert(\'XSS\')">'
    resp = client.get("/echo", params={"msg": malicious_img})
    
    # Проверяем что HTML теги полностью удалены
    assert "<img" not in resp.text
    assert "onerror" not in resp.text
    assert 'alert(\'XSS\')' in resp.text  # Текст остается
    assert resp.status_code == 200

def test_xss_multiple_vectors_blocked():
    """GWT: Различные XSS векторы блокируются"""
    xss_vectors = [
        '<svg onload=alert(1)>',
        '<body onload=alert(1)>', 
        '<iframe src=javascript:alert(1)>',
        '<a href="javascript:alert(1)">click</a>'
    ]
    
    for vector in xss_vectors:
        resp = client.get("/echo", params={"msg": vector})
        
        # Проверяем что HTML теги удалены
        assert "<" not in resp.text, f"HTML tags should be removed: {vector}"
        assert resp.status_code == 200
