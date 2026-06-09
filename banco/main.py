from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from banco.api.routes import router
from datetime import datetime, timezone

app = FastAPI(title="Banco — Banking System", version="1.0.0")
app.include_router(router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
