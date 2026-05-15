import streamlit as st
from vectorstore import search_codebase
from ingestor import fetch_github_repo
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize ChromaDB client (same as vectorstore)
@st.cache_resource
def init_chroma():
    client = chromadb.PersistentClient(path="./chroma_db")
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="codebase",
        embedding_function=embedding_fn
    )
    return collection

st.set_page_config(page_title="Codebase Q&A Agent", layout="wide")

st.title("🤖 Codebase Q&A Agent")
st.markdown("Ask questions about any GitHub repository")

# Sidebar for repo input
with st.sidebar:
    st.header("📦 Repository Settings")
    repo_url = st.text_input(
        "GitHub Repo URL",
        placeholder="https://github.com/tiangolo/fastapi",
        value="https://github.com/tiangolo/fastapi"
    )
    
    if st.button("🔄 Load / Reload Repository"):
        with st.spinner(f"Fetching and indexing {repo_url}..."):
            from vectorstore import index_repo
            index_repo(repo_url)
        st.success("Repository indexed successfully!")
        st.rerun()
    
    st.divider()
    st.caption("Built with Groq + LangChain + ChromaDB")

# Main chat interface
st.header("💬 Ask about the codebase")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Example: How does routing work in FastAPI?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get answer from vectorstore
    with st.chat_message("assistant"):
        with st.spinner("Searching codebase..."):
            results = search_codebase(prompt, n_results=3)
            
            # Format response
            response = "### 📚 Found relevant code:\n\n"
            for i, doc in enumerate(results["documents"][0]):
                file_path = results["metadatas"][0][i]["path"]
                response += f"**{i+1}. File: `{file_path}`**\n\n"
                response += f"```python\n{doc[:500]}...\n```\n\n"
            
            st.markdown(response)
            
            # Add to history
            st.session_state.messages.append({"role": "assistant", "content": response})