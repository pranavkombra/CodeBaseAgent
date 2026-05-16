import streamlit as st
from vectorstore import search_codebase, collection
from ingestor import fetch_github_repo
from doc_generator import generate_documentation, fetch_file_content
from test_generator import extract_functions, generate_tests, save_tests_to_file
import os
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="CodeBase Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main header gradient */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Stats box */
    .stats-box {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .stat-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e9ecef;
    }
    
    .stat-item:last-child {
        border-bottom: none;
    }
    
    .stat-label {
        font-weight: 600;
        color: #495057;
    }
    
    .stat-value {
        color: #667eea;
        font-weight: 700;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }
    
    /* Toast messages */
    .success-toast {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .info-toast {
        background: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
    
    /* Code blocks */
    .stCodeBlock {
        border-radius: 8px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #6c757d;
        font-size: 0.875rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "collection_loaded" not in st.session_state:
    st.session_state.collection_loaded = False
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []
if "indexed_python_files" not in st.session_state:
    st.session_state.indexed_python_files = []
if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_repo" not in st.session_state:
    st.session_state.current_repo = ""

# Function to load collection data
def load_collection_data():
    """Load and cache collection data in session state"""
    try:
        all_data = collection.get()
        file_paths = []
        python_files = []
        
        if all_data and all_data.get("metadatas"):
            metadatas = all_data["metadatas"]
            if metadatas:
                file_paths_set = set()
                python_files_set = set()
                
                for meta in metadatas:
                    if meta and "path" in meta:
                        path = meta["path"]
                        if isinstance(path, str):
                            file_paths_set.add(path)
                            if path.endswith(".py"):
                                python_files_set.add(path)
                
                file_paths = sorted(list(file_paths_set))
                python_files = sorted(list(python_files_set))
        
        st.session_state.indexed_files = file_paths
        st.session_state.indexed_python_files = python_files
        st.session_state.total_chunks = len(all_data.get("ids", [])) if all_data else 0
        st.session_state.collection_loaded = True
        
    except Exception as e:
        st.error(f"Error loading collection: {str(e)}")
        st.session_state.collection_loaded = False

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 CodeBase Agent")
    st.markdown("---")
    
    # Repository input
    st.markdown("#### 📦 Repository")
    repo_url = st.text_input(
        "GitHub URL",
        placeholder="https://github.com/owner/repo",
        value=st.session_state.current_repo if st.session_state.current_repo else "https://github.com/tiangolo/fastapi",
        label_visibility="collapsed"
    )
    
    # Load button
    if st.button("🔄 Load Repository", type="primary", use_container_width=True):
        with st.spinner(f"🔍 Fetching and indexing repository..."):
            try:
                from vectorstore import index_repo
                index_repo(repo_url)
                st.session_state.current_repo = repo_url
                load_collection_data()
                st.success("✅ Repository indexed successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    
    # Stats box
    if st.session_state.collection_loaded:
        st.markdown("#### 📊 Statistics")
        st.markdown(f"""
        <div class="stats-box">
            <div class="stat-item">
                <span class="stat-label">📄 Files Indexed</span>
                <span class="stat-value">{len(st.session_state.indexed_files)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">🐍 Python Files</span>
                <span class="stat-value">{len(st.session_state.indexed_python_files)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">📦 Total Chunks</span>
                <span class="stat-value">{st.session_state.total_chunks}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Load a repository to see statistics")
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div class="footer">
        <small>Built by pranav k s<br/>
        pranavkombra@gmail.com</small>
    </div>
    """, unsafe_allow_html=True)

# Main content
st.markdown("""
<div class="main-header">
    <h1>🤖 CodeBase Agent</h1>
    <p>AI-powered code analysis, documentation, and test generation</p>
</div>
""", unsafe_allow_html=True)

# Load collection data on startup if not loaded
if not st.session_state.collection_loaded:
    load_collection_data()

# Create tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📝 Documentation", "🧪 Tests"])

# ==================== TAB 1: CHAT ====================
with tab1:
    st.markdown("### 💬 Ask About the Codebase")
    st.markdown("Ask questions and get relevant code snippets from the indexed repository.")
    
    if not st.session_state.collection_loaded or len(st.session_state.indexed_files) == 0:
        st.warning("⚠️ No repository loaded. Please load a repository from the sidebar first.")
    else:
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Example: How does routing work in this codebase?"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get answer from vectorstore
            with st.chat_message("assistant"):
                with st.spinner("🔍 Searching codebase..."):
                    results = search_codebase(prompt, n_results=3)
                    
                    # Format response
                    response = "### 📚 Found Relevant Code:\n\n"
                    if results and results.get("documents") and results.get("metadatas"):
                        documents = results["documents"]
                        metadatas = results["metadatas"]
                        if documents and metadatas and len(documents) > 0 and len(metadatas) > 0:
                            for i, doc in enumerate(documents[0]):
                                file_path = metadatas[0][i].get("path", "Unknown")
                                response += f"**{i+1}. File: `{file_path}`**\n\n"
                                response += f"```python\n{doc[:500]}...\n```\n\n"
                        else:
                            response = "❌ No relevant code found. Try rephrasing your question."
                    else:
                        response = "❌ No relevant code found. Try rephrasing your question."
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

# ==================== TAB 2: DOCUMENTATION ====================
with tab2:
    st.markdown("### 📝 Documentation Generator")
    st.markdown("Generate comprehensive markdown documentation for any file in the indexed codebase.")
    
    if not st.session_state.collection_loaded or len(st.session_state.indexed_files) == 0:
        st.warning("⚠️ No files indexed. Please load a repository from the sidebar first.")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_file = st.selectbox(
                "Select a file to document:",
                options=st.session_state.indexed_files,
                key="doc_file_selector"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            generate_btn = st.button("🚀 Generate Docs", type="primary", use_container_width=True)
        
        # Generate documentation
        if generate_btn and selected_file:
            with st.spinner(f"✨ Generating documentation for `{selected_file}`..."):
                documentation = generate_documentation(selected_file, st.session_state.current_repo)
                st.session_state.generated_doc = documentation
                st.session_state.doc_filename = selected_file.replace("/", "_").replace(".py", ".md")
        
        # Display generated documentation
        if "generated_doc" in st.session_state:
            st.markdown("---")
            st.markdown("#### 📄 Generated Documentation")
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                if st.button("📋 Copy", use_container_width=True):
                    st.code(st.session_state.generated_doc, language="markdown")
                    st.success("✅ Ready to copy!")
            
            with col2:
                st.download_button(
                    label="💾 Download",
                    data=st.session_state.generated_doc,
                    file_name=st.session_state.doc_filename,
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # Display documentation
            st.markdown(st.session_state.generated_doc)

# ==================== TAB 3: TESTS ====================
with tab3:
    st.markdown("### 🧪 Unit Test Generator")
    st.markdown("Generate pytest unit tests for any function in the indexed Python files.")
    
    if not st.session_state.collection_loaded or len(st.session_state.indexed_python_files) == 0:
        st.warning("⚠️ No Python files indexed. Please load a repository from the sidebar first.")
    else:
        col1, col2 = st.columns([2, 2])
        
        with col1:
            selected_test_file = st.selectbox(
                "Select a Python file:",
                options=st.session_state.indexed_python_files,
                key="test_file_selector"
            )
        
        # Fetch and extract functions
        if selected_test_file:
            file_content = fetch_file_content(st.session_state.current_repo, selected_test_file)
            
            if file_content:
                functions = extract_functions(file_content)
                
                if functions:
                    function_names = [f"{func[0]} (line 0)" for func in functions]
                    
                    with col2:
                        selected_function_display = st.selectbox(
                            "Select a function:",
                            options=function_names,
                            key="function_selector"
                        )
                    
                    # Extract function name
                    selected_function_name = selected_function_display.split(" (line")[0]
                    selected_function = next((f for f in functions if f[0] == selected_function_name), None)
                    
                    if selected_function:
                        # Function preview
                        with st.expander("📄 View Function Code", expanded=False):
                            st.code(selected_function[1], language="python")
                        
                        # Generate button
                        col1_btn, col2_btn, col3_btn = st.columns([1, 1, 2])
                        with col1_btn:
                            generate_test_btn = st.button("🚀 Generate Tests", type="primary", use_container_width=True)
                        
                        # Generate tests
                        if generate_test_btn:
                            with st.spinner(f"✨ Generating tests for `{selected_function_name}`..."):
                                test_code = generate_tests(
                                function_name=selected_function_name,
                                function_code=selected_function[1],  # ← CORRECT (tuple)
                                repo_url=...
)
                                st.session_state.generated_tests = test_code
                                st.session_state.test_original_file = selected_test_file
                        
                        # Display generated tests
                        if "generated_tests" in st.session_state:
                            st.markdown("---")
                            st.markdown("#### 🧪 Generated Unit Tests")
                            
                            # Action buttons
                            col1, col2, col3 = st.columns([1, 1, 4])
                            
                            with col1:
                                if st.button("📋 Copy", key="copy_tests", use_container_width=True):
                                    st.code(st.session_state.generated_tests, language="python")
                                    st.success("✅ Ready to copy!")
                            
                            with col2:
                                if st.button("💾 Save File", key="save_tests", use_container_width=True):
                                    saved_path = save_tests_to_file(
                                        st.session_state.generated_tests,
                                        st.session_state.test_original_file
                                    )
                                    if saved_path:
                                        st.success(f"✅ Saved to: `{saved_path}`")
                                    else:
                                        st.error("❌ Failed to save tests")
                            
                            # Display test code
                            st.code(st.session_state.generated_tests, language="python", line_numbers=True)
                else:
                    st.info("ℹ️ No functions found in the selected file.")
            else:
                st.error(f"❌ Could not fetch content for `{selected_test_file}`")

# Made with Bob
