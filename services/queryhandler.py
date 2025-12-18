async def handle_user_query(data, model):
    user_query = data.get("query")
    query_embedding = model.encode(user_query)
    candidate_ids = search_faiss(query_embedding, top_k=5)
    product_metadata = get_product_metadata(candidate_ids)

    if not product_metadata:
        source_url = data.get("source_url")
        if source_url:
            scraped_data = scrape_amazon_data(source_url)
            if scraped_data:
                extra_data = data.get("extra_data", {})
                product_id = candidate_ids[0] if candidate_ids else int(time.time())
                update_graph_with_scrape(product_id, scraped_data, extra_data)
                product_metadata = get_product_metadata([product_id])

    llm_response = query_gemini_llm(product_metadata, user_query)
    return llm_response, product_metadata
