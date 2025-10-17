
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_echo_should_escape_script_tags():
    """GWT: Отражённая XSS не исполняется для script тегов"""
    resp = client.get("/echo", params={"msg": "<script>alert(1)</script>"})
    
    # После strip_all_html должен остаться только текст "alert(1)"
    assert "<script>" not in resp.text
    assert "&lt;script&gt;" not in resp.text  # Даже экранированные теги не должны быть
    assert "alert(1)" in resp.text  # Только текстовое содержимое
    assert resp.status_code == 200

def test_img_onerror_not_executed():
    """GWT: XSS через img onerror не исполняется"""
    malicious_img = '<img src="x" onerror="alert(\'XSS\')">'
    resp = client.get("/echo", params={"msg": malicious_img})
    
    # Должен остаться только чистый текст без HTML
    assert "<img" not in resp.text
    assert "onerror" not in resp.text
    assert 'alert(\'XSS\')' in resp.text  # Текст содержимого остается
    assert 'src="x"' not in resp.text  # Атрибуты удалены
    assert resp.status_code == 200

def test_xss_multiple_vectors_blocked():
    """GWT: Различные XSS векторы блокируются"""
    xss_vectors = [
        ('<svg onload=alert(1)>', 'alert(1)'),  # вектор → ожидаемый текст
        ('<body onload=alert(1)>', 'alert(1)'),
        ('<iframe src=javascript:alert(1)>', 'alert(1)'),
        ('<a href="javascript:alert(1)">click</a>', 'click'),  # текст ссылки остается
    ]
    
    for vector, expected_text in xss_vectors:
        resp = client.get("/echo", params={"msg": vector})
        
        # Проверяем что HTML теги удалены, но текст остается
        assert "<" not in resp.text or "&lt;" in resp.text, f"HTML tags should be removed: {vector}"
        assert expected_text in resp.text, f"Text content should remain: {vector}"
        assert resp.status_code == 200
