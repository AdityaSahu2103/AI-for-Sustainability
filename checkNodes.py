import os
from neo4j import GraphDatabase

# Replace these with your Neo4j Aura connection details.
NEO4J_URI = "neo4j+s://ecc7573b.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sjPz6CGB_LveDlc19j-M2dW1pV1Y9fr3m0QFcuDOcKs")

def check_product_nodes():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Query all Product nodes; limit if needed for performance.
        result = session.run("MATCH (p:Product) RETURN p LIMIT 100")
        products = []
        for record in result:
            node = record["p"]
            # Convert node properties to a dictionary for easy viewing.
            products.append(dict(node))
        return products

if __name__ == "__main__":
    products = check_product_nodes()
    for idx, product in enumerate(products):
        print(f"\n--- Product {idx+1} ---")
        for key, value in product.items():
            print(f"{key}: {value}")
