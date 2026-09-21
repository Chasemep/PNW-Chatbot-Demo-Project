"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="Purdue Policy Chatbot")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
