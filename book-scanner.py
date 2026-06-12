import sqlite3
import cv2
from neo4j import GraphDatabase
from pyzbar.pyzbar import decode
import requests

# --- CONFIGURATION ---
SQLITE_DB = "local_library.db"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "yournewpassword"  # Change to your Neo4j password


# --- DATABASE INITIALIZATION ---
def init_databases():
    # Initialize SQLite
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            isbn TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            publish_date TEXT
        )
    """
    )
    conn.commit()
    conn.close()
    print("SQLite Initialized.")


# --- STEP 1: BARCODE SCANNING ---
def scan_barcode_from_webcam():
    print("Opening webcam... Point the book barcode at the camera. Press 'q' to quit.")
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Decode any barcodes in the frame
        detected_barcodes = decode(frame)
        for barcode in detected_barcodes:
            isbn = barcode.data.decode("utf-8")
            if len(isbn) in [10, 13]:  # Standard ISBN lengths
                print(f"Captured ISBN: {isbn}")
                cap.release()
                cv2.destroyAllWindows()
                return isbn

        cv2.imshow("Barcode Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None


# --- STEP 2: FETCH BOOK METADATA ---
def fetch_book_data(isbn):
    print(f"Fetching data for ISBN: {isbn}...")
    # Using the free Open Library API
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json"
    response = requests.get(url).json()

    key = f"ISBN:{isbn}"
    if key in response:
        data = response[key]
        # Extract fields safely
        title = data.get("title", "Unknown Title")
        publish_date = data.get("publish_date", "Unknown Date")
        authors = [auth["name"] for auth in data.get("authors", [])]
        author = authors[0] if authors else "Unknown Author"

        return {
            "isbn": isbn,
            "title": title,
            "author": author,
            "publish_date": publish_date,
        }
    return None


# --- STEP 3 & 4: HUMAN VERIFICATION & SAVING ---
def save_to_databases(book):
    # 1. Save to SQLite
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?)",
            (book["isbn"], book["title"], book["author"], book["publish_date"]),
        )
        conn.commit()
        print("Saved to SQLite local database.")
    except sqlite3.IntegrityError:
        print("Book already exists in SQLite.")
    finally:
        conn.close()

    # 2. Save to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Cypher query to create Book, Author, and the relationship
        query = """
        MERGE (a:Author {name: $author_name})
        MERGE (b:Book {isbn: $isbn, title: $title, publish_date: $pub_date})
        MERGE (a)-[:WROTE]->(b)
        """
        session.run(
            query,
            author_name=book["author"],
            isbn=book["isbn"],
            title=book["title"],
            pub_date=book["publish_date"],
        )
        print("Saved and linked in Neo4j Graph database.")
    driver.close()


# --- MAIN LOOP ---
def main():
    init_databases()

    # Scan
    isbn = scan_barcode_from_webcam()
    if not isbn:
        print("No valid barcode scanned.")
        return

    # Fetch
    book_profile = fetch_book_data(isbn)
    if not book_profile:
        print("Could not find book data online. Creating blank profile.")
        book_profile = {
            "isbn": isbn,
            "title": "",
            "author": "",
            "publish_date": "",
        }

    # Human Verification Step
    print("\n--- BOOK PROFILE PREVIEW ---")
    print(f"ISBN:         {book_profile['isbn']}")
    print(f"1. Title:     {book_profile['title']}")
    print(f"2. Author:    {book_profile['author']}")
    print(f"3. Pub. Date:  {book_profile['publish_date']}")
    print("--------------------------------")

    correct = (
        input("Is this information correct? (yes/no/edit): ").strip().lower()
    )

    if correct in ["edit", "no"]:
        book_profile["title"] = (
            input(f"Enter Title [{book_profile['title']}]: ")
            or book_profile["title"]
        )
        book_profile["author"] = (
            input(f"Enter Author [{book_profile['author']}]: ")
            or book_profile["author"]
        )
        book_profile["publish_date"] = (
            input(f"Enter Pub Date [{book_profile['publish_date']}]: ")
            or book_profile["publish_date"]
        )

    # Save
    print("\nSaving to local storage...")
    save_to_databases(book_profile)
    print("Done!")


if __name__ == "__main__":
    main()