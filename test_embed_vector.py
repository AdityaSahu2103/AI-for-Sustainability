from main import model, index, faiss_id_map
import numpy as np

product_id = "vector123"
text = "Eco-friendly sustainable perfume for men that smells amazing."

vector = model.encode(text).astype('float32')
index.add(np.array([vector]))
faiss_id_map.append(product_id)

print("✅ Vector added. Total vectors in FAISS:", index.ntotal)
print("FAISS ID Map:", faiss_id_map)
