import streamlit as st
from vectorstore import search_codebase, collection
from ingestor import fetch_github_repo
from doc_generator import generate_documentation
import os
from dotenv import load_dotenv

load_dotenv()

# Use the collection from vectorstore to ensure consistency
@st.cache_resource
def init_chroma():
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
            
            # Format response with null checks
            response = "### 📚 Found relevant code:\n\n"
            if results and results.get("documents") and results.get("metadatas"):
                documents = results["documents"]
                metadatas = results["metadatas"]
                if documents and metadatas and len(documents) > 0 and len(metadatas) > 0:
                    for i, doc in enumerate(documents[0]):
                        file_path = metadatas[0][i].get("path", "Unknown")
                        response += f"**{i+1}. File: `{file_path}`**\n\n"
                        response += f"```python\n{doc[:500]}...\n```\n\n"
                else:
                    response = "No relevant code found. Please index a repository first."
            else:
                response = "No relevant code found. Please index a repository first."
            
            st.markdown(response)
            
            # Add to history
            st.session_state.messages.append({"role": "assistant", "content": response})

# Documentation Generator Section
st.divider()
st.header("📝 Documentation Generator")
st.markdown("Generate comprehensive documentation for any file in the indexed codebase")

# Get all unique file paths from the collection
collection = init_chroma()
try:
    all_data = collection.get()
    file_paths = []
    if all_data and all_data.get("metadatas"):
        # Extract unique file paths with type safety
        metadatas = all_data["metadatas"]
        if metadatas:
            # Filter out None values and ensure we have strings
            file_paths_set = set()
            for meta in metadatas:
                if meta and "path" in meta:
                    path = meta["path"]
                    if isinstance(path, str):
                        file_paths_set.add(path)
            file_paths = sorted(list(file_paths_set))
    
    if file_paths:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_file = st.selectbox(
                    "Select a file to document:",
                    options=file_paths,
                    key="doc_file_selector"
                )
            
            with col2:
                st.write("")  # Spacing
                st.write("")  # Spacing
                generate_btn = st.button("🚀 Generate Documentation", type="primary", use_container_width=True)
            
            # Generate documentation when button is clicked
            if generate_btn and selected_file:
                with st.spinner(f"Generating documentation for {selected_file}..."):
                    documentation = generate_documentation(selected_file, repo_url)
                    st.session_state.generated_doc = documentation
                    st.session_state.doc_filename = selected_file.replace("/", "_").replace(".py", ".md")
            
            # Display generated documentation
            if "generated_doc" in st.session_state:
                st.divider()
                st.subheader("📄 Generated Documentation")
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 4])
                
                with col1:
                    # Copy button
                    if st.button("📋 Copy", use_container_width=True):
                        st.code(st.session_state.generated_doc, language="markdown")
                        st.success("Documentation ready to copy!")
                
                with col2:
                    # Download button
                    st.download_button(
                        label="💾 Save as .md",
                        data=st.session_state.generated_doc,
                        file_name=st.session_state.doc_filename,
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                # Display the documentation
                st.markdown(st.session_state.generated_doc)
    else:
        st.info("No files indexed yet. Please load a repository first.")
except Exception as e:
    st.error(f"Error loading files: {str(e)}")