#!/usr/bin/env python3
"""
VaultGuard REST API — Centralized secrets management via Firebase Firestore.

Endpoints:
  GET  /secrets         — List all secret keys (masked values)
  GET  /secrets/{key}   — Get a specific secret value
  PUT  /secrets/{key}   — Set/update a secret
  DELETE /secrets/{key} — Delete a secret
  GET  /health          — Health check
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
import uvicorn
from datetime import datetime, timezone

logger = logging.getLogger("vaultguard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Firebase init
cred_path = os.environ.get("FIREBASE_CREDENTIALS", "service_account.json")
if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()

db = firestore.client()
COLLECTION = "secrets"
API_KEY = os.environ.get("VAULTGUARD_API_KEY", "")

if not API_KEY:
    logger.warning("⚠️  VAULTGUARD_API_KEY is empty — all endpoints are UNPROTECTED")

app = FastAPI(title="VaultGuard", description="Centralized secrets management")


def verify_key(x_api_key: str = Header("")):
    """Dependency: validate API key on every protected endpoint."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class SecretPayload(BaseModel):
    value: str
    category: str = ""


@app.get("/secrets")
async def list_secrets(_=Depends(verify_key)):
    logger.info("LIST secrets")
    docs = db.collection(COLLECTION).stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        results.append({
            "key": doc.id,
            "category": d.get("category", "unknown"),
            "preview": d.get("value", "")[:4] + "..." if d.get("value") else "empty",
            "updated_at": str(d.get("updated_at", "")),
        })
    return {"secrets": results, "count": len(results)}


@app.get("/secrets/{key}")
async def get_secret(key: str, _=Depends(verify_key)):
    logger.info("GET secret: %s", key)
    doc = db.collection(COLLECTION).document(key).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Secret '{key}' not found")
    return {"key": key, "value": doc.to_dict().get("value", "")}


@app.put("/secrets/{key}")
async def set_secret(key: str, payload: SecretPayload, _=Depends(verify_key)):
    logger.info("SET secret: %s", key)
    # Infer category from key name
    category = payload.category
    if not category:
        kl = key.lower()
        if any(x in kl for x in ["tradier", "tasty", "schwab"]):
            category = "brokerage"
        elif any(x in kl for x in ["gemini", "openai", "anthropic"]):
            category = "ai"
        elif any(x in kl for x in ["stripe"]):
            category = "billing"
        elif any(x in kl for x in ["firebase", "gcp", "google"]):
            category = "cloud"
        elif any(x in kl for x in ["telegram", "discord", "twitter"]):
            category = "social"
        else:
            category = "other"

    db.collection(COLLECTION).document(key).set({
        "value": payload.value,
        "category": category,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": os.environ.get("HOSTNAME", "unknown"),
    })
    return {"status": "ok", "key": key, "category": category}


@app.delete("/secrets/{key}")
async def delete_secret(key: str, _=Depends(verify_key)):
    logger.warning("DELETE secret: %s", key)
    doc = db.collection(COLLECTION).document(key).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Secret '{key}' not found")
    db.collection(COLLECTION).document(key).delete()
    return {"status": "deleted", "key": key}


@app.get("/health")
async def health():
    try:
        # Verify Firestore connectivity
        db.collection(COLLECTION).limit(1).get()
        return {"status": "ok", "service": "vaultguard", "collection": COLLECTION, "firestore": "connected"}
    except Exception as e:
        return {"status": "degraded", "service": "vaultguard", "error": str(e)[:100]}


if __name__ == "__main__":
    port = int(os.environ.get("VAULTGUARD_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
