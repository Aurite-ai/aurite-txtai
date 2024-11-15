from src.services.embeddings_service import EmbeddingsService

def main():
    # Test data
    documents = [
        "US tops 5 million confirmed virus cases",
        "Canada's last fully intact ice shelf has suddenly collapsed, forming a Manhattan-sized iceberg",
        "Beijing mobilises invasion craft along coast as Taiwan tensions escalate",
        "The National Park Service warns against sacrificing slower friends in a bear attack",
        "Maine man wins $1M from $25 lottery ticket",
        "Make huge profits without work, earn up to $100,000 a day"
    ]
    
    search = EmbeddingsService()
    
    # Index test documents
    print("Indexing documents...")
    search.add(documents)
    
    # Test simple search
    query = "climate change"
    print(f"\nSimple search for: {query}")
    results = search.simple_search(query)
    for score, text in results:
        print(f"{score:.4f} {text}")
    
    # Test hybrid search
    print(f"\nHybrid search for: {query}")
    results = search.hybrid_search(query)
    for result in results:
        print(f"Text: {result['text']}")
        print(f"Semantic: {result['scores']['semantic']:.4f}")
        print(f"Keyword: {result['scores']['keyword']:.4f}\n")

if __name__ == "__main__":
    main() 