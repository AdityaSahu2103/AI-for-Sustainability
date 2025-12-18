# 🌱 EcoSmart Shopping Assistant

An intelligent browser extension and backend system that helps users discover eco-friendly products and find local sustainable vendors. The system uses AI-powered semantic search, graph databases, and real-time product analysis to provide personalized sustainability recommendations.

## ✨ Features

- **🤖 AI-Powered Product Recommendations**: Get intelligent suggestions for eco-friendly alternatives using Google Gemini AI
- **🔍 Semantic Product Search**: Vector-based similarity search using FAISS for finding relevant products
- **📊 Graph Database Integration**: Neo4j-powered knowledge graph for storing and querying product relationships
- **🌐 Browser Extension**: Chrome extension that works seamlessly on Amazon product pages
- **🗺️ Local Vendor Discovery**: Interactive map showing eco-friendly vendors in Hyderabad
- **📦 Product Scraping**: Automated extraction of product data, reviews, and sustainability features from Amazon
- **💬 Context-Aware Chat**: Chatbot that understands the current product page context

## 🏗️ Architecture

```
┌─────────────────┐
│ Browser Extension│
│  (Chrome)        │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────────┬─────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌────────┐  ┌──────┐
│FAISS │  │Neo4j │  │ Gemini │  │Selenium│
│Index │  │Graph │  │   AI   │  │Scraper │
└──────┘  └──────┘  └────────┘  └──────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework for building APIs
- **FAISS**: Facebook AI Similarity Search for vector similarity matching
- **Neo4j**: Graph database for product relationship management
- **Sentence Transformers**: For generating semantic embeddings (`all-MiniLM-L6-v2`)
- **Google Gemini AI**: Large language model for generating recommendations
- **Selenium**: Web scraping for product data extraction
- **BeautifulSoup**: HTML parsing

### Frontend
- **Chrome Extension API**: Browser extension functionality
- **JavaScript**: Extension logic and UI
- **Leaflet.js**: Interactive maps for vendor locations
- **HTML/CSS**: Extension popup and content script UI

### Data Processing
- **Pandas**: Data manipulation and CSV processing
- **NumPy**: Numerical operations for embeddings

## 📋 Prerequisites

- Python 3.8+
- Google Chrome browser
- Neo4j database (cloud or local instance)
- Google Gemini API key
- ChromeDriver (automatically managed by webdriver-manager)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd HackIndia_2k25
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you encounter issues with `faiss-cpu`, you may need to install it separately:
```bash
pip install faiss-cpu
# or for GPU support
pip install faiss-gpu
```

### 4. Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
NEO4J_PASSWORD=your_neo4j_password_here
```

### 5. Neo4j Setup

Update the Neo4j connection details in `main.py`:
- URI: `neo4j+s://ecc7573b.databases.neo4j.io` (or your instance)
- Username: `neo4j`
- Password: Set in `.env` file

### 6. Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the project root directory
5. The extension should now be installed

## 🎯 Usage

### Starting the Backend Server

```bash
python main.py
```

The server will start on `http://127.0.0.1:8000`

### Using the Browser Extension

1. Navigate to any Amazon product page (e.g., `amazon.in`)
2. Click the extension icon or look for the floating chatbot button
3. Ask questions about eco-friendly alternatives or product sustainability
4. View vendor locations on the interactive map

### Example Queries

- "What are eco-friendly alternatives to this product?"
- "Show me sustainable clothing options"
- "Find local vendors for eco-friendly electronics"
- "What sustainability features does this product have?"

## 📡 API Endpoints

### `POST /query`
Process user queries and return AI-generated recommendations.

**Request Body:**
```json
{
  "query": "Find eco-friendly alternatives",
  "context": {
    "name": "Product Name",
    "price": "999",
    "currency": "₹",
    "rating": "4.5",
    "sustainabilityFeatures": ["Organic", "Recyclable"]
  }
}
```

**Response:**
```json
{
  "answer": "AI-generated response...",
  "metadata": [...],
  "vendor_data": {
    "center": {"lat": 17.385044, "lng": 78.486671},
    "vendors": [...]
  }
}
```

### `POST /update`
Manually add or update product data in the graph.

### `GET /faiss-status`
Check the status of the FAISS index (vector count, mapped IDs).

### `POST /import-dataset-batch`
Import products from CSV in batches.

**Query Parameters:**
- `batch_size`: Number of products to process (default: 200)
- `start`: Starting index (default: 2000)

### `GET /vendors/{category}`
Get vendor locations for a specific category.

**Categories:** `clothing`, `electronics`, `home`, `beauty`, `general`

## 📁 Project Structure

```
HackIndia_2k25/
│
├── main.py                 # FastAPI backend server
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .gitignore             # Git ignore rules
│
├── manifest.json           # Chrome extension manifest
├── popup.html             # Extension popup UI
├── popup.js               # Popup logic
├── background.js          # Extension background service worker
├── content.js             # Content script for Amazon pages
├── content.css            # Content script styles
│
├── services/
│   └── queryhandler.py    # Query processing logic
│
├── vendor_map/            # Vendor mapping resources
│   ├── map.html
│   ├── map.js
│   └── vendors.js
│
├── vendor_search.py       # Vendor search API (alternative)
│
├── test_*.py              # Test scripts
│
└── data files:
    ├── cleaned_greendb.csv        # Product dataset
    ├── faiss_index.bin           # FAISS vector index
    └── faiss_id_map.pkl          # ID mapping for vectors
```

## 🔧 Configuration

### FAISS Index
- **Dimension**: 384 (for `all-MiniLM-L6-v2` model)
- **Index Type**: `IndexFlatL2` (L2 distance)
- **Storage**: `faiss_index.bin` and `faiss_id_map.pkl`

### Selenium Scraping
- **Headless Mode**: Enabled
- **Browser**: Chrome (configured path in code)
- **Timeout**: 10 seconds for element waits

### Gemini AI
- **Model**: `gemini-1.5-pro-latest`
- **Context**: Includes product metadata, reviews, and sustainability features

## 🧪 Testing

Run individual test scripts:
```bash
python test_faiss.py
python test_neo4j.py
python test_gemini.py
python test_scrape.py
```

## 📊 Data Flow

1. **Product Ingestion**:
   - CSV dataset → Selenium scraping → Neo4j graph + FAISS index

2. **Query Processing**:
   - User query → Embedding → FAISS search → Neo4j metadata → Gemini AI → Response

3. **Browser Extension**:
   - Page context extraction → API call → Display response + vendor map

## 🌍 Vendor Mapping

The system includes a vendor mapping feature that shows eco-friendly vendors in Hyderabad:
- **Categories**: Clothing, Electronics, Home, Beauty, General
- **Map Provider**: OpenStreetMap (via Leaflet.js)
- **Data Source**: Static vendor data (can be extended with Overpass API)

## 🔒 Security Notes

- **CORS**: Currently set to allow all origins (`*`). Restrict for production.
- **API Keys**: Never commit `.env` file to version control.
- **Neo4j Credentials**: Store securely, use environment variables.

## 🐛 Troubleshooting

### Extension Not Working
- Ensure backend server is running on `http://127.0.0.1:8000`
- Check browser console for errors
- Verify extension is enabled in Chrome

### FAISS Index Issues
- Delete `faiss_index.bin` and `faiss_id_map.pkl` to recreate
- Ensure sufficient disk space

### Neo4j Connection Errors
- Verify credentials in `.env`
- Check network connectivity to Neo4j instance
- Ensure Neo4j database is running

### Scraping Failures
- Update ChromeDriver path if needed
- Check if Amazon page structure has changed
- Verify internet connectivity

## 🚧 Future Enhancements

- [ ] Support for multiple e-commerce platforms
- [ ] Real-time vendor data from Overpass API
- [ ] User authentication and personalized recommendations
- [ ] Product comparison features
- [ ] Sustainability scoring system
- [ ] Mobile app version
- [ ] Multi-language support



