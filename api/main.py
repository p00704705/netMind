import os
import sys

# Add the parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="NetMind API",
    version="1.0.0",
    description="Expose NetMind backend functions via REST API",
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8123)
