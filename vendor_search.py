# vendor_search.py
from fastapi import FastAPI, HTTPException, Query
import requests
import logging
from typing import Dict
import math

logging.basicConfig(level=logging.DEBUG)

app = FastAPI(
    title="Vendor Search API",
    description="Fetches nearby vendors using Overpass API based on location and query filters"
)

def meters_to_degrees(meters: float) -> float:
    # Approximately 1 degree latitude ≈ 111 km.
    return meters / 111000.0

def get_dynamic_shop_filter(query: str) -> str:
    """
    Returns an Overpass shop filter based on the input query.
    If the query suggests a specific vendor type (e.g., 'repair', 'water bottle'),
    a corresponding filter is applied; otherwise, the generic shop filter is used.
    """
    query_lower = query.strip().lower()
    # Mapping some keywords to common vendor types:
    keyword_filter_map = {
        "repair": '["shop"~"repair|service",i]',
        "car": '["shop"~"car_repair|auto",i]',
        "water bottle": '["shop"~"supermarket|convenience|drinks|water",i]',
        "bottle": '["shop"~"supermarket|convenience|drinks|water",i]'
    }
    for keyword, shop_filter in keyword_filter_map.items():
        if keyword in query_lower:
            logging.debug("Matched keyword '%s', using filter: %s", keyword, shop_filter)
            return shop_filter
    # If query is non-empty but no specific match, use generic query filter
    if query_lower:
        generic_filter = f'["shop"~"{query_lower}",i]'
        logging.debug("Using generic filter: %s", generic_filter)
        return generic_filter
    return '["shop"]'

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Rough Euclidean distance; sufficient for sorting within a small area.
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

def calculate_relevance(vendor: dict, query: str) -> float:
    """
    Compute a simple relevance score based on whether the query string 
    is found in the vendor's name or shop type.
    """
    score = 0
    query_lower = query.lower()
    if query_lower in vendor.get("name", "").lower():
        score += 1
    if query_lower in vendor.get("shop", "").lower():
        score += 1
    return score

@app.get("/vendors")
def get_vendors(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
    radius: int = Query(5000, description="Search radius in meters (default 5000 m)"),
    query: str = Query("", description="Optional vendor query filter (e.g., repair, water bottle)")
) -> Dict[str, object]:
    """
    Uses the Overpass API to fetch vendor data within a bounding box defined 
    by the given location and radius. Applies a dynamic shop filter based on the query.
    The results are scored by relevance (based on query match) and distance.
    Returns a JSON object with a list of vendors and their count.
    """
    # Calculate bounding box.
    radius_deg = meters_to_degrees(radius)
    south = lat - radius_deg
    north = lat + radius_deg
    west = lon - radius_deg
    east = lon + radius_deg

    shop_filter = get_dynamic_shop_filter(query)
    
    # Build the Overpass query.
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node{shop_filter}({south},{west},{north},{east});
      way{shop_filter}({south},{west},{north},{east});
      relation{shop_filter}({south},{west},{north},{east});
    );
    out center;
    """
    logging.debug("Overpass Query:\n%s", overpass_query)
    
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": overpass_query}, timeout=30)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Overpass API error: " + response.text)
        data = response.json()
        vendors = []
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            vendor = {
                "name": tags.get("name", "Unknown"),
                "shop": tags.get("shop", "Unknown")
            }
            if "center" in element:
                vendor["lat"] = element["center"]["lat"]
                vendor["lon"] = element["center"]["lon"]
            else:
                vendor["lat"] = element.get("lat")
                vendor["lon"] = element.get("lon")
            vendors.append(vendor)
        
        # Score vendors by relevance and distance.
        for vendor in vendors:
            if vendor.get("lat") is None or vendor.get("lon") is None:
                vendor["distance"] = float('inf')
                vendor["relevance"] = 0
            else:
                vendor["distance"] = calculate_distance(lat, lon, vendor["lat"], vendor["lon"])
                vendor["relevance"] = calculate_relevance(vendor, query) if query.strip() else 0

        # Sort vendors: prioritize those with higher relevance; if equal, sort by distance.
        vendors_sorted = sorted(vendors, key=lambda v: (-v["relevance"], v["distance"]))
        
        logging.debug("Found %d vendors after sorting", len(vendors_sorted))
        return {"vendors": vendors_sorted, "count": len(vendors_sorted)}
    except Exception as e:
        logging.exception("Error fetching vendor data:")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)
