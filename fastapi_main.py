import uvicorn
from fastapi import FastAPI

from api.v1.planning import planning_router

app = FastAPI()
app.include_router(planning_router)

if __name__ == "__main__":
    uvicorn.run("fastapi_main:app", host="0.0.0.0", port=11211, reload=True)
