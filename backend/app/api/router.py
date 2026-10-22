from fastapi import APIRouter

from app.api.routes import auth, discussions, meta, search, tags

api = APIRouter(prefix="/api/v1")
api.include_router(auth.router)
api.include_router(discussions.router)
api.include_router(tags.router)
api.include_router(search.router)
api.include_router(meta.router)
