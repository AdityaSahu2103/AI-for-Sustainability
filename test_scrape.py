from main import scrape_amazon_data
import logging


# Replace with a known Amazon product URL for testing
test_url = "https://www.amazon.co.uk/Sloggi-Womens-Microfibre-Hipster-Blueberry/dp/B0BKLN189Y/ref=sr_1_156"  
result = scrape_amazon_data(test_url)
print("Scraped Data:", result)
