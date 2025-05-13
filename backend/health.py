from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_200_OK

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint that explicitly supports both GET and HEAD methods
@app.get("/health")
@app.head("/health")
def health_check():
    return JSONResponse(content={"status": "ok"})

# Root endpoint that supports both GET and HEAD
@app.get("/")
@app.head("/")
def root():
    # For HEAD requests, return an empty response with 200 status code
    return Response(status_code=HTTP_200_OK)
