from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from neo4j import GraphDatabase
import requests

app = FastAPI()

# Database Config (Same as before)
SQLITE_DB = "local_library.db"
NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "yournewpassword"

class BookScan(BaseModel):
    isbn: str

def fetch_and_save(isbn):
    # ... Insert  exact 'fetch_book_data' and 'save_to_databases' 
    # logic from  previous working script here ...
    pass

@app.post("/scan")
def receive_scan(data: BookScan):
    try:
        # Run your existing fetch & save functions
        result = fetch_and_save(data.isbn) 
        return {"status": "success", "message": f"Book {data.isbn} cataloged!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # This runs the server on your local home Wi-Fi network
    uvicorn.run(app, host="0.0.0.0", port=8000)