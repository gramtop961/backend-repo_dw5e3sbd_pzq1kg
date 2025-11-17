import os
from typing import Optional, List, Dict, Any
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import create_document, get_documents

app = FastAPI(title="Pokemon TCG Checker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PTCG_API_BASE = "https://api.pokemontcg.io/v2"
CARDMARKET_API_BASE = "https://api.cardmarket.com/ws/v2.0"  # Placeholder base; public price scraping not supported without OAuth

class WishlistIn(BaseModel):
    card_id: str
    name: str
    set_name: Optional[str] = None
    set_id: Optional[str] = None
    number: Optional[str] = None
    image_url: Optional[str] = None
    desired_price: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = "watching"

@app.get("/")
def root():
    return {"message": "Pokemon TCG Checker Backend running"}

@app.get("/test")
def test_database():
    """Test endpoint to check database connectivity"""
    from database import db
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ---------- Pokemon TCG API proxy endpoints ----------

@app.get("/api/cards")
def search_cards(
    q: Optional[str] = Query(None, description="Pokemon TCG API query, e.g., name:Charizard set.id:sv3"),
    page: int = 1,
    pageSize: int = 24,
):
    """Proxy search to Pokemon TCG API with passthrough query.
    Docs: https://docs.pokemontcg.io/
    """
    try:
        params = {"page": page, "pageSize": pageSize}
        if q:
            params["q"] = q
        r = requests.get(f"{PTCG_API_BASE}/cards", params=params, timeout=20)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cards/{card_id}")
def get_card(card_id: str):
    try:
        r = requests.get(f"{PTCG_API_BASE}/cards/{card_id}", timeout=20)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sets")
def list_sets(page: int = 1, pageSize: int = 50, orderBy: Optional[str] = None):
    try:
        params: Dict[str, Any] = {"page": page, "pageSize": pageSize}
        if orderBy:
            params["orderBy"] = orderBy
        r = requests.get(f"{PTCG_API_BASE}/sets", params=params, timeout=20)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Prices (Cardmarket placeholder) ----------
# Cardmarket requires OAuth 1.0a credentials; without keys, we cannot call it directly.
# For now, expose a structure and return informative error if not configured.

@app.get("/api/prices/cardmarket/{card_id}")
def get_cardmarket_price(card_id: str):
    """Placeholder endpoint for Cardmarket prices.
    If credentials are provided via env (CARDMARKET_APP_TOKEN, APP_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET),
    this can be extended. Currently returns 501 if not configured.
    """
    app_token = os.getenv("CARDMARKET_APP_TOKEN")
    if not app_token:
        raise HTTPException(status_code=501, detail="Cardmarket API not configured. Provide OAuth credentials to enable.")
    # Future: implement OAuth1 call here
    raise HTTPException(status_code=501, detail="Cardmarket integration pending implementation.")

# ---------- Wishlist endpoints (Mongo-backed) ----------

@app.post("/api/wishlist")
def add_wishlist(item: WishlistIn):
    try:
        doc_id = create_document("wishlistitem", item)
        return {"id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/wishlist")
def list_wishlist(status: Optional[str] = None):
    try:
        filter_dict = {"status": status} if status else {}
        docs = get_documents("wishlistitem", filter_dict=filter_dict)
        # Convert ObjectId to string if present
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
