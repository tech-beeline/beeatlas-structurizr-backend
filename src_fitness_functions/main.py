from fastapi import FastAPI
import logging
import uvicorn

app = FastAPI(
    title="Fitness-functions API",
    description="Base fitness functions for application architecture control",
    version="1.0.0"
)

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

from api import health
from api import ff_adr_01

app.include_router(health.router)
app.include_router(ff_adr_01.router)

uvicorn.run(app, host="0.0.0.0", port=8080)
