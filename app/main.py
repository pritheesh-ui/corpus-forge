from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import chats, files, pages


def create_app() -> FastAPI:
    init_db()

    app = FastAPI(title="Document Chat")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.include_router(pages.router)
    app.include_router(files.router)
    app.include_router(chats.router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
