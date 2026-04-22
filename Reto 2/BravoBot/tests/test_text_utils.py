from app.utils.text import chunk_text, clean_text, infer_category


def test_clean_text_normalizes_whitespace() -> None:
    text = "Hola\n\n   mundo   !"
    assert clean_text(text) == "Hola mundo!"


def test_chunk_text_creates_multiple_chunks() -> None:
    text = " ".join([f"palabra{i}" for i in range(120)])
    chunks = chunk_text(text, chunk_size=40, chunk_overlap=5)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)


def test_infer_category_uses_url_keywords() -> None:
    assert infer_category("https://pascualbravo.edu.co/admisiones", "") == "admisiones"