from fastapi import APIRouter
from .documents import router as documents_router
from .document_groups import router as document_groups_router
from .document_tags import router as document_tags_router
from .chat import router as chat_router
from .search import router as search_router

api_router = APIRouter()

# Include all API routers
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(document_groups_router, prefix="/document-groups", tags=["document-groups"])
api_router.include_router(document_tags_router, prefix="/document-tags", tags=["document-tags"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(search_router, prefix="/search", tags=["search"])
