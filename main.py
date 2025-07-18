import os
import re
import requests
from bs4 import BeautifulSoup
from editionguard import (
    editionguard_product_exists,
    editionguard_create_product
)
from dotenv import load_dotenv

load_dotenv()

SHOP_NAME = os.getenv("SHOPIFY_SHOP_NAME")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_EBOOKS_PATH = os.getenv("S3_EBOOKS_PATH")
S3_REGION = os.getenv("S3_BUCKET_REGION")
LOCAL_EBOOKS_PATH = os.getenv("LOCAL_EBOOKS_PATH")

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": ACCESS_TOKEN
}

BASE_URL = f"https://{SHOP_NAME}.myshopify.com/admin/api/2024-04"

# Configure AWS CLI using read credentials
os.system(f"aws configure set aws_access_key_id {AWS_ACCESS_KEY}")
os.system(f"aws configure set aws_secret_access_key {AWS_SECRET_KEY}")
os.system(f"aws configure set default.region {S3_REGION}")
os.system('aws configure set output json')

# Download ebooks from S3 using AWS CLI
print('Downloading ebooks from S3...')
cmd = f"aws s3 sync 's3://{S3_BUCKET}/{S3_EBOOKS_PATH}/' '{LOCAL_EBOOKS_PATH}'"
os.system(cmd)

def get_all_products():
    products = []
    url = f"{BASE_URL}/products.json?limit=250"
    while url:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        products.extend(data.get("products", []))

        link = resp.headers.get("Link", "")
        if 'rel="next"' in link:
            import re
            match = re.search(r'<([^>]+)>; rel="next"', link)
            url = match.group(1) if match else None
        else:
            break
    return products

def get_ebook_variants(product):
    return [v for v in product.get("variants", []) if "eBook" in v.get("title", "")]

def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("metafields")

def get_metafield_value(metafields, namespace="editionguard", key="resource_id"):
    for m in metafields:
        if m.get("key") == key and m.get("namespace") == namespace:
            return m.get("value")
    return None

def set_metafield(product_id, value, namespace="editionguard", key="resource_id", value_type="single_line_text_field"):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    data = {
        "metafield": {
            "namespace": namespace,
            "key": key,
            "type": value_type,
            "value": value
        }
    }
    resp = requests.post(url, json=data, headers=HEADERS)
    if resp.status_code not in [200, 201]:
        print(f"Failed to save metafield: {resp.status_code} — {resp.text}")

def get_ebook_local_path(eisbn):
    return f"{LOCAL_EBOOKS_PATH}/{eisbn}.pdf"

def main():
    print("Fetching Shopify products...")
    products = get_all_products()
    print(f"Total products fetched: {len(products)}")
    total_ebooks = 0

    for product in products:
        ebook_variants = get_ebook_variants(product)
        if not ebook_variants:
            continue

        product_id = product["id"]
        plain_text = BeautifulSoup(product.get("body_html", ""), "html.parser").get_text(separator=" ").strip()
        isbn_match = re.search(r"ISBN \(eBook\):\s*([\d\-]{10,})", plain_text)
        ebook_isbn = isbn_match.group(1).replace("-", "") if isbn_match else None

        metafields = get_metafields(product_id)
        resource_id = get_metafield_value(metafields)

        for variant in ebook_variants:
            product_id = variant.get("product_id")
            if not product_id:
                print(f"Skipping variant without product_id in product '{product['title']}'")
                continue

            total_ebooks += 1
            #print(f"\nProcessing eBook variant: {product['title']} — Product Id: {product_id}")

            if not resource_id:
                if not ebook_isbn:
                    print(f"Could not extract ISBN (eBook) from product '{product['title']}'")
                    continue

                res = editionguard_create_product(product['title'], ebook_isbn, get_ebook_local_path(ebook_isbn))
                if res is not None:
                    resource_id = res.get("resource_id")
                    set_metafield(product_id, res.get("resource_id"))
            else:
                if not editionguard_product_exists(resource_id):
                    print(f"EditionGuard product MISSING for Product Id '{product_id}' – check for sync issues")

    print(f"\nTotal eBook variants processed: {total_ebooks}")


if __name__ == "__main__":
    main()
