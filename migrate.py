import os
import requests

from main import (
    get_metafields,
    get_metafield_value
)
from editionguard import (
    editionguard_send_email
)
from dotenv import load_dotenv

load_dotenv()

EDITIONGUARD_API_KEY = os.getenv("EDITIONGUARD_API_KEY")
EDITIONGUARD_API_URL = "https://app.editionguard.com/api/v2"
SHOP_NAME = os.getenv("SHOPIFY_SHOP_NAME")
SHOPIFY_DOMAIN = f"{SHOP_NAME}.myshopify.com"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
ORDER_NUMBERS = []

url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/orders.json"

headers = {
    "X-Shopify-Access-Token": ACCESS_TOKEN
}

for order_number in ORDER_NUMBERS:
    params = {
        "name": order_number,
        "status": "any"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        orders = response.json().get("orders", [])
        if orders:
            order = orders[0]
            customer_email = order["customer"]["email"]
            for item in order["line_items"]:
                if item["variant_title"] == "eBook":
                    product_id = item["product_id"]
                    title = item["title"]
                    metafields = get_metafields(product_id)
                    resource_id = get_metafield_value(metafields)
                    if not resource_id:
                        print(f"Resource ID not found for Product Id '{product_id}', order number '{order_number}'")
                        continue
                    res = editionguard_send_email(resource_id, customer_email, title)
                    print(res)
        else:
            print("Order not found.")
    else:
        print("Error:", response.status_code, response.text)
