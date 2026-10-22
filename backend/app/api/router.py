from fastapi import APIRouter

from app.api.routes import (
    auth,
    discussions,
    editor,
    meta,
    posts,
    search,
    tags,
    uploads,
    users,
)

api = APIRouter(prefix="/api/v1")
api.include_router(auth.router)
api.include_router(discussions.router)
api.include_router(posts.router)
api.include_router(editor.router)
api.include_router(tags.router)
api.include_router(users.router)
api.include_router(uploads.router)
api.include_router(search.router)
api.include_router(meta.router)
