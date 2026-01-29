from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routers import auth, pos, dashboard, products

app = FastAPI(title="Veggie POS V3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(pos.router, prefix="/api", tags=["POS"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(products.router, prefix="/api", tags=["Products"]) # New Router

@app.get("/")
def root():
    return {"status": "System Online", "version": "3.0.0"}