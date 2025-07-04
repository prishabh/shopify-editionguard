import os
import requests
from dotenv import load_dotenv

load_dotenv()

EDITIONGUARD_API_KEY = os.getenv("EDITIONGUARD_API_KEY")
EDITIONGUARD_API_URL = "https://app.editionguard.com/api/v2"

def editionguard_product_exists(resource_id):
    """Check if a product with the given SKU exists on EditionGuard."""
    url = f"{EDITIONGUARD_API_URL}/book/{resource_id}"
    HEADERS = {
        "Authorization": f"Bearer {EDITIONGUARD_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return True
    return False

def editionguard_create_product(title, ebook_isbn, local_pdf_path):
    """
    Uploads a book to EditionGuard using multipart/form-data.
    `local_pdf_path` should be the path to a local file (e.g. downloaded from S3).
    """
    url = f"{EDITIONGUARD_API_URL}/book"
    headers = {
        "Authorization": f"Bearer {EDITIONGUARD_API_KEY}",
    }

    files = {
        "resource": (os.path.basename(local_pdf_path), open(local_pdf_path, "rb"), "application/pdf")
    }
    data = {
        "title": title,
        "publisher": "Ethics International Press",
        "isbn13": ebook_isbn
    }

    print(f"Uploading: {title} with ISBN {ebook_isbn} to EditionGuard...")

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code in [200, 201]:
            print(f"Created EditionGuard book: {title}")
            return response.json()
        else:
            print(f"Failed to create book: {response.status_code} — {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error creating book: {e}")
        return None

