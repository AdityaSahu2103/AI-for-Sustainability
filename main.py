from bs4 import BeautifulSoup
import logging
import requests
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from neo4j import GraphDatabase
import pandas as pd
import time
import json
from google.generativeai import GenerativeModel, configure
import os
from dotenv import load_dotenv
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import re
import concurrent.futures
import math
from typing import Dict, List
import random

# ------------------ FastAPI Setup ------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

# ----------------- Environment and Gemini Setup -----------------
load_dotenv()  # Load .env variables
configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = GenerativeModel("gemini-1.5-pro-latest")

# ----------------- Initialize SentenceTransformer Model -----------------
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logging.debug("Sentence Transformer model loaded successfully.")
except Exception as e:
    logging.exception("Failed to load Sentence Transformer model: %s", e)

# ----------------- Initialize FAISS Index and ID Map -----------------
dimension = 384  # Embedding dimension for 'all-MiniLM-L6-v2'
FAISS_INDEX_FILE = "faiss_index.bin"
ID_MAP_FILE = "faiss_id_map.pkl"

# Attempt to load existing FAISS index and ID map from disk.
try:
    if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(ID_MAP_FILE):
        logging.info("📦 Loading FAISS index and ID map from disk...")
        index = faiss.read_index(FAISS_INDEX_FILE)
        with open(ID_MAP_FILE, "rb") as f:
            faiss_id_map = pickle.load(f)
    else:
        raise FileNotFoundError
except Exception as e:
    logging.warning("Could not load FAISS index from disk (%s); creating a new index.", e)
    index = faiss.IndexFlatL2(dimension)
    faiss_id_map = []

# ----------------- Neo4j Connection Setup -----------------
neo4j_uri = "neo4j+s://ecc7573b.databases.neo4j.io"
neo4j_user = "neo4j"
neo4j_password = os.getenv("NEO4J_PASSWORD") or "sjPz6CGB_LveDlc19j-M2dW1pV1Y9fr3m0QFcuDOcKs"
try:
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    logging.debug("Connected to Neo4j at %s", neo4j_uri)
except Exception as e:
    logging.exception("Failed to connect to Neo4j: %s", e)

# ----------------- Helper Functions -----------------

def search_faiss(query_embedding, top_k=5):
    """
    Performs vector similarity search using FAISS.
    Returns a list of matched product_ids from faiss_id_map.
    """
    print("Total vectors in FAISS:", index.ntotal)
    print("FAISS → Product Map:", faiss_id_map)
    try:
        query_embedding = np.array([query_embedding]).astype('float32')
        distances, indices = index.search(query_embedding, top_k)
        logging.debug("FAISS returned raw indices: %s, distances: %s", indices[0], distances[0])
        matched_product_ids = []
        for idx in indices[0]:
            if idx != -1 and idx < len(faiss_id_map):
                matched_product_ids.append(faiss_id_map[idx])
            else:
                matched_product_ids.append(None)
        logging.debug("Mapped FAISS indices to product IDs: %s", matched_product_ids)
        return matched_product_ids
    except Exception as e:
        logging.exception("Error during FAISS search: %s", e)
        return []

def scrape_amazon_data(url):
    """
    Uses Selenium to load an Amazon product page and then uses BeautifulSoup
    to parse the fully rendered HTML. Returns a dictionary with:
      - name, description, price, currency, rating, review_count,
      - asin, image_urls, reviews,
      - sustainability_certified, and eco_features.
    """
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("window-size=1920,1080")
        options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # --- Extract Product Title using Selenium ---
        try:
            title_elem = wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
            name = title_elem.text.strip()
        except TimeoutException:
            name = "Unknown Title"

        # --- Extract Description using Selenium ---
        try:
            desc_elem = driver.find_element(By.ID, "productDescription")
            description = desc_elem.text.strip()
        except NoSuchElementException:
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, "#feature-bullets")
                description = desc_elem.text.strip()
            except NoSuchElementException:
                description = "No description available."

        # --- Extract Price using Selenium ---
        try:
            price_whole = driver.find_element(By.CLASS_NAME, "a-price-whole").text.strip()
            price_frac = driver.find_element(By.CLASS_NAME, "a-price-fraction").text.strip()
            price = f"{price_whole}.{price_frac}"
        except NoSuchElementException:
            price = "N/A"

        # --- Extract Currency using Selenium ---
        try:
            currency_elem = driver.find_element(By.CLASS_NAME, "a-price-symbol")
            currency = currency_elem.text.strip()
        except NoSuchElementException:
            currency = "₹"

        # --- Extract Rating using BeautifulSoup ---
        temp_bsoup = BeautifulSoup(driver.page_source, "html.parser")
        rating_elem = temp_bsoup.find("span", class_="a-icon-alt")
        rating = rating_elem.get_text().strip() if rating_elem else "No Rating Available"
        
        # --- Extract Review Count using Selenium ---
        try:
            review_count_elem = driver.find_element(By.ID, "acrCustomerReviewText")
            review_count = review_count_elem.text.strip()
        except NoSuchElementException:
            review_count = "0 reviews"

        # --- Extract ASIN ---
        asin = "N/A"
        try:
            asin_match = re.search(r"/dp/([A-Z0-9]{10})", url)
            if asin_match:
                asin = asin_match.group(1)
        except Exception:
            pass

        # --- Extract Image URLs using Selenium ---
        image_urls = []
        try:
            main_img = driver.find_element(By.ID, "landingImage")
            src = main_img.get_attribute("src")
            if src:
                image_urls.append(src)
        except NoSuchElementException:
            pass
        try:
            alt_images_div = driver.find_element(By.ID, "altImages")
            img_tags = alt_images_div.find_elements(By.TAG_NAME, "img")
            alt_image_urls = [tag.get_attribute("src") for tag in img_tags if tag.get_attribute("src")]
            image_urls.extend(alt_image_urls)
        except NoSuchElementException:
            pass
        image_urls = list(set(image_urls))

        # --- Extract Top 5 Reviews using Selenium ---
        reviews = []
        try:
            review_blocks = driver.find_elements(By.CSS_SELECTOR, "span[data-hook='review-body']")
            reviews = [rev.text.strip() for rev in review_blocks[:5] if rev.text.strip()]
        except NoSuchElementException:
            reviews = []

        # --- For Sustainability Extraction, use BeautifulSoup on the full page source ---
        page_source = driver.page_source
        bsoup = BeautifulSoup(page_source, "html.parser")
        sustainability_certified = False
        eco_features = []
        try:
            sustainability_section = bsoup.find(string=lambda text: text and "sustainability features" in text.lower())
            if sustainability_section:
                parent = sustainability_section.find_parent()
                if parent:
                    sustainability_certified = True
                    feature_items = parent.find_all_next("li", limit=5)
                    if not feature_items:
                        feature_items = parent.find_all_next("p", limit=5)
                    for item in feature_items:
                        text_val = item.get_text(strip=True)
                        if text_val and text_val not in eco_features:
                            eco_features.append(text_val)
        except Exception as ex:
            logging.exception("Error extracting sustainability features via BeautifulSoup: %s", ex)
            sustainability_certified = False
            eco_features = ["Not specified"]

        driver.quit()

        scraped_data = {
            "name": name,
            "description": description,
            "price": price,
            "currency": currency,
            "rating": rating,
            "review_count": review_count,
            "asin": asin,
            "image_urls": image_urls,
            "reviews": reviews,
            "sustainability_certified": sustainability_certified,
            "eco_features": eco_features
        }
        logging.debug("Scrape result: %s", scraped_data)
        return scraped_data

    except Exception as e:
        logging.exception("Selenium scraping failed: %s", e)
        return None

def update_graph_with_scrape(product_id, scraped_data, extra_data):
    """
    Updates the Neo4j graph with the combined product data.
    Also generates a semantic embedding (using name, description, and top 3 reviews),
    adds it to the FAISS index, and maps the product_id.
    """
    try:
        combined_data = {**extra_data, **scraped_data}

        def flatten_and_clean_labels(lst):
            cleaned = []
            for item in lst:
                if isinstance(item, list):
                    cleaned.extend(flatten_and_clean_labels(item))
                elif isinstance(item, str):
                    if item.startswith("[") and item.endswith("]"):
                        try:
                            import ast
                            parsed = ast.literal_eval(item)
                            if isinstance(parsed, list):
                                cleaned.extend([str(i).strip() for i in parsed])
                            else:
                                cleaned.append(str(parsed).strip())
                        except Exception:
                            cleaned.append(item.strip())
                    else:
                        cleaned.append(item.strip())
                else:
                    cleaned.append(str(item).strip())
            return cleaned

        sustainability_certified = extra_data.get("sustainability_certified", [])
        eco_features = extra_data.get("eco_features", [])

        if isinstance(sustainability_certified, str):
            sustainability_certified = [sustainability_certified]
        if isinstance(eco_features, str):
            eco_features = [eco_features]

        sustainability_labels = flatten_and_clean_labels(sustainability_certified + eco_features)

        logging.debug("Updating graph for product %s with data: %s", product_id, combined_data)
        with driver.session() as session:
            session.run("""
                MERGE (p:Product {id: $id})
                SET p += {
                    name: $name,
                    description: $description,
                    reviews: $reviews,
                    categories: $categories,
                    gender: $gender,
                    timestamp: $timestamp,
                    url: $url,
                    source: $source,
                    merchant: $merchant,
                    country: $country,
                    brand: $brand,
                    sustainability_labels: $sustainability_labels,
                    price: $price,
                    currency: $currency,
                    image_urls: $image_urls,
                    consumer_lifestage: $consumer_lifestage,
                    colors: $colors,
                    sizes: $sizes,
                    gtin: $gtin,
                    asin: $asin,
                    product_text: $product_text,
                    rating: $rating,
                    review_count: $review_count
                }
            """, 
            id=product_id,
            name=combined_data.get("name"),
            description=combined_data.get("description"),
            reviews=combined_data.get("reviews"),
            categories=combined_data.get("categories", ""),
            gender=combined_data.get("gender", ""),
            timestamp=combined_data.get("timestamp", time.time()),
            url=combined_data.get("url", ""),
            source=combined_data.get("source", ""),
            merchant=combined_data.get("merchant", ""),
            country=combined_data.get("country", "IN"),
            brand=combined_data.get("brand", ""),
            sustainability_labels=sustainability_labels,
            price=combined_data.get("price", ""),
            currency=combined_data.get("currency", ""),
            image_urls=combined_data.get("image_urls", ""),
            consumer_lifestage=combined_data.get("consumer_lifestage", ""),
            colors=combined_data.get("colors", ""),
            sizes=combined_data.get("sizes", ""),
            gtin=combined_data.get("gtin", ""),
            asin=combined_data.get("asin", ""),
            product_text=combined_data.get("product_text", ""),
            rating=combined_data.get("rating", ""),
            review_count=combined_data.get("review_count", "")
        )
        logging.debug("Graph updated successfully for product %s", product_id)

        name_text = combined_data.get("name", "")
        description_text = combined_data.get("description", "")
        reviews_text = " ".join(combined_data.get("reviews", [])[:3])
        product_text_for_embedding = f"{name_text} {description_text} {reviews_text}".strip()
        logging.debug("Text for embedding: %s", product_text_for_embedding)

        if product_text_for_embedding:
            vector = model.encode(product_text_for_embedding).astype('float32')
            index.add(np.array([vector]))
            faiss_id_map.append(product_id)

            faiss.write_index(index, FAISS_INDEX_FILE)
            with open(ID_MAP_FILE, "wb") as f:
                pickle.dump(faiss_id_map, f)

            logging.debug("FAISS index and ID map updated for product %s at position %d", product_id, len(faiss_id_map) - 1)
        else:
            logging.warning("Empty product text for embedding; FAISS not updated for product %s", product_id)

    except Exception as e:
        logging.exception("Error updating graph with scraped data: %s", e)

def get_product_metadata(product_ids):
    """
    Fetches metadata for given product IDs from the Neo4j graph.
    """
    metadata_list = []
    with driver.session() as session:
        for pid in product_ids:
            try:
                result = session.run("MATCH (p:Product {id: $pid}) RETURN p", pid=pid)
                record = result.single()
                if record:
                    product = record["p"]
                    metadata = dict(product)
                    metadata_list.append(metadata)
                    logging.debug("Found metadata for product id %s: %s", pid, metadata)
                else:
                    logging.debug("No metadata found for product id %s", pid)
            except Exception as e:
                logging.exception("Error retrieving metadata for product id %s: %s", pid, e)
    return metadata_list

def query_gemini_llm(metadata_list, user_query, current_context=None):
    """
    Constructs a detailed context prompt using user query, product metadata, and current page context,
    and calls the Gemini API for a final, polished, and well-formatted answer.
    """
    try:
        context = f"User Query: {user_query}\n\n"
        
        if current_context:
            context += (
                "Current Product Context:\n"
                f"📦 Product: {current_context.get('name', 'N/A')}\n"
                f"💰 Price: {current_context.get('price', 'N/A')} {current_context.get('currency', '')}\n"
                f"⭐ Rating: {current_context.get('rating', 'N/A')}\n"
                f"🌿 Sustainability Features: {', '.join(current_context.get('sustainabilityFeatures', ['None specified']))}\n\n"
            )

        context += (
            "You are an expert product assistant. Based on the details below and the current product context, provide an informative, "
            "well-written answer addressing the user's question. Focus particularly on sustainability comparisons and eco-friendly alternatives "
            "when relevant.\n\n"
            "IMPORTANT: For every product recommendation, always end your response with:\n"
            "'Find local vendors for [category] products in Hyderabad' where category matches the type of product (clothing, electronics, home, beauty, or general).\n\n"
            "If the user is viewing a product, try to provide specific recommendations in relation to that product. "
            "Focus on inferred details from descriptions, reviews, and sustainability info.\n\n"
            "Use bullet points where appropriate. Keep the tone professional, structured, and reader-friendly.\n\n"
            "Relevant Product Information from Database:\n"
        )

        for product in metadata_list:
            context += f"📦 Product Name: {product.get('name', 'N/A')}\n"
            context += f"💬 Description: {product.get('description', 'No Description')}\n"
            context += f"💰 Price: {product.get('price', 'N/A')} {product.get('currency', '')}\n"
            context += f"⭐ Rating: {product.get('rating', 'N/A')} ({product.get('review_count', 'No reviews')})\n"

            sustainability = product.get('sustainability_labels', [])
            if sustainability:
                context += "🌿 Sustainability Features:\n"
                for label in sustainability:
                    context += f"  - {label}\n"

            context += "📝 Top Reviews:\n"
            for review in product.get('reviews', [])[:3]:
                context += f"  - {review}\n"

            context += "\n"

        logging.debug("Final Gemini Prompt:\n%s", context)

        response = gemini_model.generate_content(context)
        return response.text

    except Exception as e:
        logging.exception("Failed to query Gemini: %s", e)
        return "Sorry, I'm having trouble processing your query right now."

def sanitize_metadata(metadata_list):
    for item in metadata_list:
        for key, value in item.items():
            if isinstance(value, float) and math.isnan(value):
                item[key] = None
    return metadata_list

# --- Helper function for concurrent dataset row processing ---
def process_dataset_row(row, idx):
    """
    Processes a single dataset row:
      - Extracts URL, calls scrape_amazon_data.
      - Processes sustainability features.
      - Calls update_graph_with_scrape.
    Returns a dict with success info or error details.
    """
    product_id = f"green-{idx}"
    url = row.get("url")
    if not url or pd.isnull(url):
        return {"row": idx, "error": "Missing URL"}
    
    scraped = scrape_amazon_data(url)
    if not scraped:
        return {"row": idx, "url": url, "error": "Scraping failed"}

    scraped_certified = scraped.get("sustainability_certified", [])
    scraped_eco_features = scraped.get("eco_features", [])
    if isinstance(scraped_certified, bool):
        scraped_certified = ["Certified"] if scraped_certified else []
    elif isinstance(scraped_certified, str):
        scraped_certified = [scraped_certified]
    
    combined = []
    if row.get("sustainability_labels"):
        combined += row.get("sustainability_labels").split(";")
    combined += scraped_certified + scraped_eco_features

    clean_labels = []
    for label in combined:
        if isinstance(label, list):
            clean_labels.extend(label)
        else:
            clean_labels.append(str(label).strip())

    extra_data = {
        "categories": row.get("category", ""),
        "gender": row.get("gender", ""),
        "timestamp": time.time(),
        "url": url,
        "source": row.get("source", ""),
        "merchant": row.get("merchant", ""),
        "country": row.get("country", "IN"),
        "brand": row.get("brand", ""),
        "sustainability_labels": clean_labels,
        "sustainability_certified": scraped_certified,
        "eco_features": scraped_eco_features,
        "consumer_lifestage": row.get("consumer_lifestage", ""),
        "colors": row.get("colors", ""),
        "sizes": row.get("sizes", ""),
        "gtin": row.get("gtin", ""),
        "product_text": row.get("product_text", "")
    }

    update_graph_with_scrape(product_id, scraped, extra_data)
    return {"row": idx, "success": product_id}

# Add this before the FastAPI endpoints
def get_hyderabad_vendors(category: str) -> List[Dict]:
    """Returns a static list of eco-friendly vendors in Hyderabad based on category."""
    # Hyderabad center coordinates
    center = {"lat": 17.385044, "lng": 78.486671}
    
    # Static vendor data with slight coordinate variations
    vendors = {
        "clothing": [
            {"name": "Eco Threads", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.5, "type": "Sustainable Fashion"},
            {"name": "Green Wardrobe", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.2, "type": "Organic Clothing"},
            {"name": "Earth Fashion", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.0, "type": "Eco Fashion"}
        ],
        "electronics": [
            {"name": "Green Gadgets", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.3, "type": "Eco Electronics"},
            {"name": "Sustainable Tech", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.1, "type": "Green Technology"},
            {"name": "EcoTech Solutions", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.4, "type": "Sustainable Electronics"}
        ],
        "home": [
            {"name": "Eco Home", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.6, "type": "Home Goods"},
            {"name": "Green Living", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.3, "type": "Sustainable Home"},
            {"name": "Eco Decor", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.2, "type": "Home Decor"}
        ],
        "beauty": [
            {"name": "Natural Beauty", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.7, "type": "Organic Beauty"},
            {"name": "Eco Cosmetics", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.4, "type": "Natural Cosmetics"},
            {"name": "Green Beauty", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.5, "type": "Sustainable Beauty"}
        ],
        "general": [
            {"name": "Eco Store", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.4, "type": "General Eco Goods"},
            {"name": "Green Market", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.2, "type": "Sustainable Products"},
            {"name": "Earth Essentials", "lat": 17.385044 + random.uniform(-0.02, 0.02), "lng": 78.486671 + random.uniform(-0.02, 0.02), "rating": 4.3, "type": "Eco Products"}
        ]
    }
    
    return {
        "center": center,
        "vendors": vendors.get(category.lower(), vendors["general"])
    }

# ------------------ FastAPI Endpoints ------------------

@app.post("/query")
async def query_endpoint(request: Request):
    """
    Processes a user query with optional product context from browser extension:
      1. Computes the query embedding
      2. Performs FAISS search for candidate product IDs
      3. Retrieves product metadata from Neo4j
      4. Uses gathered data and current context to query Gemini API
      5. Returns the final answer
    """
    try:
        data = await request.json()
        user_query = data.get("query")
        current_context = data.get("context")
        
        query_embedding = model.encode(user_query)
        candidate_ids = search_faiss(query_embedding, top_k=5)
        product_metadata = get_product_metadata(candidate_ids)
        product_metadata = sanitize_metadata(product_metadata)

        if not product_metadata and current_context:
            product_metadata = [current_context]
        
        llm_response = query_gemini_llm(product_metadata, user_query, current_context)
        
        # Extract category from the response
        category_match = re.search(r"Find local vendors for (\w+) products", llm_response)
        vendor_data = None
        if category_match:
            category = category_match.group(1).lower()
            vendor_data = get_hyderabad_vendors(category)
        
        return JSONResponse({
            "answer": llm_response,
            "metadata": product_metadata,
            "vendor_data": vendor_data
        })
    except Exception as e:
        logging.exception("Error in /query endpoint: %s", e)
        return JSONResponse({"error": "Internal server error"}, status_code=500)

@app.post("/update")
async def update_endpoint(request: Request):
    """
    Allows manual addition or update of product data in the graph.
    """
    try:
        new_product_data = await request.json()
        logging.debug("Received update data: %s", new_product_data)
        product_id = new_product_data.get("id", str(int(time.time())))
        update_graph_with_scrape(product_id, new_product_data, new_product_data)
        return JSONResponse({"status": "Graph updated successfully"})
    except Exception as e:
        logging.exception("Error in /update endpoint: %s", e)
        return JSONResponse({"error": "Internal server error"}, status_code=500)

def load_greendb_dataset(file_path):
    """
    Loads the greendb dataset from a CSV file and logs its basic statistics.
    """
    try:
        logging.debug("Loading greendb dataset from: %s", file_path)
        df = pd.read_csv(file_path)
        logging.debug("Dataset loaded with %d rows and %d columns", df.shape[0], df.shape[1])
        return df
    except Exception as e:
        logging.exception("Error loading greendb dataset: %s", e)
        return None

@app.get("/faiss-status")
def faiss_status():
    try:
        return {
            "vector_count": index.ntotal,
            "mapped_ids": faiss_id_map
        }
    except Exception as e:
        logging.exception("Error in /faiss-status route: %s", e)
        return {"error": "Something went wrong."}

@app.post("/import-dataset-batch")
def import_dataset_batch(batch_size: int = 200, start: int = 2000):
    """
    Imports a batch from the greendb CSV file, processes the batch concurrently,
    scrapes data from Amazon for each row, and updates the Neo4j graph and FAISS index.
    """
    try:
        df = pd.read_csv("cleaned_greendb.csv")
        total = len(df)
        end = min(start + batch_size, total)

        logging.info(f"🚀 Processing batch from {start} to {end} of {total} rows...")
        batch = df.iloc[start:end]
        success = 0
        errors = []

        # Process rows concurrently using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Create future tasks for each row in the batch
            future_to_row = {
                executor.submit(process_dataset_row, row, i): i
                for i, row in batch.iterrows()
            }
            for future in concurrent.futures.as_completed(future_to_row):
                row_index = future_to_row[future]
                try:
                    result = future.result()
                    if result and "success" in result:
                        success += 1
                    else:
                        errors.append(result)
                except Exception as exc:
                    logging.exception("Error processing row %s: %s", row_index, exc)
                    errors.append({"row": row_index, "error": str(exc)})

        response = {
            "✅ Batch Processed": success,
            "⚠️ Errors": errors,
            "🧾 Next Batch Start": end if end < total else "✅ Done"
        }
        return JSONResponse(response)

    except Exception as e:
        logging.exception("Failed batch import")
        return {"error": str(e)}

@app.get("/vendors/{category}")
async def get_vendors(category: str):
    """
    Returns vendor locations for a given product category in Hyderabad.
    Categories: clothing, electronics, home, beauty, general
    """
    try:
        vendor_data = get_hyderabad_vendors(category)
        return JSONResponse(vendor_data)
    except Exception as e:
        logging.exception("Error getting vendor data: %s", e)
        return JSONResponse({"error": "Failed to get vendor data"}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
