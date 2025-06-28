from fastapi import FastAPI
from .database import Base, engine
from .routers import accounts, blog, like

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(accounts.router)
app.include_router(blog.router)
app.include_router(like.router) 