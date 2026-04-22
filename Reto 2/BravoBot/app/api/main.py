from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.chat_service import ChatService, build_chat_service

logger = logging.getLogger(__name__)


def create_app(chat_service: ChatService | None = None, settings: Settings | None = None) -> FastAPI:
    configure_logging()
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version=__version__, description="API oficial de BravoBot para aspirantes de la I.U. Pascual Bravo.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if chat_service is not None:
        app.state.chat_service = chat_service

    @app.on_event("startup")
    async def initialize_chat_service() -> None:
        if getattr(app.state, "chat_service", None) is None:
            app.state.chat_service = build_chat_service(settings)

    def get_service() -> ChatService:
        service = getattr(app.state, "chat_service", None)
        if service is None:
            raise RuntimeError("El servicio de chat no está inicializado.")
        return service

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        service = get_service()
        documents_indexed = 0
        try:
            documents_indexed = service.retriever.vector_store.count()
        except Exception:
            documents_indexed = 0
        return HealthResponse(
            app_name=settings.app_name,
            version=__version__,
            vector_store=service.vector_store_name,
            llm_configured=bool(settings.groq_api_key),
            documents_indexed=documents_indexed,
        )

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        try:
            return get_service().answer(request.question, session_id=request.session_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Error procesando la consulta")
            raise HTTPException(status_code=500, detail=f"No fue posible responder la consulta: {exc}") from exc

    return app


app = create_app(chat_service=None)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=False)