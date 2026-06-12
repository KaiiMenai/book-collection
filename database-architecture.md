# Configuration Guide for Local Architecture

Python application will act as the "brain" or the orchestrator.

```text
[Barcode Scanner/Camera] 
       │ (Scans ISBN)
       ▼
[Python Orchestrator] ──► [Open Library / Google Books API] (Fetch Data)
       │ 
       ▼
[GUI / Terminal Profile] ──► (Human Verification / Edits)
       │ 
       ├──► [Local SQLite DB] (Stores core book profiles & inventory)
       └──► [Local Neo4j DB]  (Stores connections: Author ── WROTE ──► Book)
```