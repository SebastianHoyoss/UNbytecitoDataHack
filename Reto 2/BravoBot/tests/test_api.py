from fastapi.testclient import TestClient

from app.api.main import create_app
from app.models.schemas import ChatResponse, HealthResponse, SourceReference


class FakeChatService:
    vector_store_name = "LocalVectorStore"

    class FakeRetriever:
        class FakeVectorStore:
            def count(self) -> int:
                return 3

        vector_store = FakeVectorStore()
        similarity_threshold = 0.24

        def build_bundle(self, question: str):
            from types import SimpleNamespace

            return SimpleNamespace(
                hits=[],
                confidence=0.0,
                context="",
            )

    retriever = FakeRetriever()

    def answer(self, question: str, session_id: str | None = None) -> ChatResponse:
        return ChatResponse(
            answer="No encontré información oficial suficiente en las fuentes disponibles de Pascual Bravo para responder con certeza.",
            sources=[SourceReference(url="https://pascualbravo.edu.co/", titulo="Inicio", score=0.91)],
            confidence=0.91,
            session_id=session_id or "test-session",
            answer_mode="fallback",
            warning="Evidencia insuficiente",
        )


def test_health_endpoint_returns_ok() -> None:
    app = create_app(chat_service=FakeChatService())
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "ok"
    assert payload.documents_indexed == 3


def test_chat_endpoint_returns_sources() -> None:
    app = create_app(chat_service=FakeChatService())
    client = TestClient(app)

    response = client.post("/chat", json={"question": "¿Cuándo son las inscripciones?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_mode"] == "fallback"
    assert payload["sources"][0]["url"].startswith("https://pascualbravo.edu.co/")