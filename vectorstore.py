import chromadb
from chromadb.utils import embedding_functions
from chromadb.api.types import EmbeddingFunction
import os
from dotenv import load_dotenv
from ingestor import fetch_github_repo
from typing import cast

load_dotenv()

# Setup ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Use SentenceTransformerEmbeddingFunction for better type compatibility
# DefaultEmbeddingFunction can cause type issues with newer ChromaDB versions
# Cast to satisfy type checker - the function is compatible at runtime
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="codebase",
    embedding_function=cast(EmbeddingFunction, embedding_fn)
)

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def index_repo(repo_url):
    print(f"Fetching repo: {repo_url}")
    files = fetch_github_repo(repo_url)
    print(f"Total files: {len(files)}")
    
    all_docs = []
    all_ids = []
    all_metadata = []
    
    for file in files:
        chunks = chunk_text(file["content"])
        for i, chunk in enumerate(chunks):
            doc_id = f"{file['path']}__chunk{i}"
            all_docs.append(chunk)
            all_ids.append(doc_id)
            all_metadata.append({"path": file["path"]})
    
    # Add to ChromaDB in batches
    batch_size = 100
    for i in range(0, len(all_docs), batch_size):
        collection.add(
            documents=all_docs[i:i+batch_size],
            ids=all_ids[i:i+batch_size],
            metadatas=all_metadata[i:i+batch_size]
        )
        print(f"Indexed {min(i+batch_size, len(all_docs))}/{len(all_docs)} chunks")
    
    print("Indexing complete!")

def search_codebase(query, n_results=5):
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results

if __name__ == "__main__":
    index_repo("https://github.com/tiangolo/fastapi")
    
    # Test search
    print("\nTesting search...")
    results = search_codebase("how does routing work")
    if results and results.get("documents") and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            print(f"\n--- Result {i+1} ---")
            if results.get("metadatas") and results["metadatas"][0]:
                print(f"File: {results['metadatas'][0][i]['path']}")
            print(doc[:200])
    else:
        print("No results found")