import numpy as np
import logging
from main import model, search_faiss, get_product_metadata

logging.basicConfig(level=logging.DEBUG)

# --- User Input Query ---
test_query = input("Enter your test query: ").strip() or "Test Product"

# --- Step 1: Generate Embedding ---
try:
    embedding = model.encode(test_query)
    logging.debug("Generated embedding for query: '%s'", test_query)
except Exception as e:
    logging.exception("Error generating embedding: %s", e)
    exit(1)

# --- Step 2: Search FAISS ---
matched_product_ids = search_faiss(embedding, top_k=5)
if not matched_product_ids:
    print("❌ No matches returned from FAISS.")
    exit(1)

# --- Step 3: Clean & Validate IDs ---
valid_ids = [pid for pid in matched_product_ids if pid is not None]
if not valid_ids:
    print("❌ No valid product IDs to retrieve metadata.")
    exit(1)

# --- Step 4: Get Metadata from Neo4j ---
metadata_list = get_product_metadata(valid_ids)
if not metadata_list:
    print("❌ No metadata found for matched products.")
else:
    print("\n🎯 Top Product Matches:\n")
    for i, product in enumerate(metadata_list, start=1):
        print(f"🔹 Match {i}:")
        print(f"  Name        : {product.get('name')}")
        print(f"  Description : {product.get('description')[:200]}...")
        print(f"  Price       : ₹{product.get('price')}")
        print(f"  Rating      : {product.get('rating')} ({product.get('review_count')} reviews)")
        print(f"  URL         : {product.get('url')}")
        print(f"  ASIN        : {product.get('asin')}")
        print("-" * 60)
