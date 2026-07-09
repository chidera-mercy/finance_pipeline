from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.database import init_pool, close_pool
from api.routers import fx, gold, inflation, interest_rates, ngx_asi, insights, indicators

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()

app = FastAPI(
    title="Nigerian Financial Data API",
    description=(
        "Serves the financial indicators and dbt mart insights "
        "produced by the finance_pipeline ELT project "
        "(exchange_rates, inflation, interest rates, gold prices, NGX All-Share Index)."
    ),
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(indicators.router)
app.include_router(fx.router)
app.include_router(gold.router)
app.include_router(inflation.router)
app.include_router(interest_rates.router)
app.include_router(ngx_asi.router)
app.include_router(insights.router)

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
