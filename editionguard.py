import os
import requests
from dotenv import load_dotenv

load_dotenv()

EDITIONGUARD_API_KEY = os.getenv("EDITIONGUARD_API_KEY")
EDITIONGUARD_API_URL = "https://app.editionguard.com/api/v2"

def editionguard_product_exists(resource_id):
    """Check if a product with the given Resource Id exists on EditionGuard."""
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

    # Check if local file exists
    if not os.path.exists(local_pdf_path):
        print(f"Local PDF file does not exist: {local_pdf_path} and title: {title}")
        return None

    files = {
        "resource": (os.path.basename(local_pdf_path), open(local_pdf_path, "rb"), "application/pdf")
    }
    data = {
        "title": title,
        "publisher": "Ethics International Press",
        "isbn13": ebook_isbn
    }

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Failed to create book {title}: {response.status_code} — {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error creating book: {e}")
        return None

def editionguard_send_email(resource_id, email, title):
    url = f"{EDITIONGUARD_API_URL}/deliver-book-link"
    headers = {
        "Authorization": f"Bearer {EDITIONGUARD_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "resource_id": resource_id,
        "email": email
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            return {"status": "sent", "email": email, "title": title}
        else:
            print(f"Failed to send email to {email} (resource_id {resource_id})")
            print(f"Status: {response.status_code}, Body: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error sending email: {e}")
        return None
