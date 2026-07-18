from fastapi import FastAPI
from db.session import engine
from api.v1.auth import router as auth_router
from api.v1.expenses import router as expenses_router
from api.v1.categories import router as categories_router
from api.v1.budgets import router as budgets_router
from api.v1.ai import router as ai_router
from db.base import init_db
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://pathfinderbookclub.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(categories_router)
app.include_router(budgets_router)
app.include_router(ai_router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "Money lens api is running"}