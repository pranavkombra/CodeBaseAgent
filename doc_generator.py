import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def fetch_file_content(repo_url, file_path):
    """
    Fetch the content of a specific file from a GitHub repository.
    
    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
        file_path: Path to the file within the repository
    
    Returns:
        File content as string, or None if fetch fails
    """
    parts = repo_url.strip("/").split("/")
    owner = parts[-2]
    repo = parts[-1]
    
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # Try master branch first, then main
    for branch in ["master", "main"]:
        file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        response = requests.get(file_url, headers=headers)
        if response.status_code == 200:
            return response.text
    
    return None

def generate_documentation(file_path, repo_url):
    """
    Generate markdown documentation for a code file using Groq API.
    
    Args:
        file_path: Path to the file within the repository
        repo_url: GitHub repository URL
    
    Returns:
        Generated documentation as markdown string
    """
    # Fetch file content
    content = fetch_file_content(repo_url, file_path)
    
    if not content:
        return f"❌ **Error**: Could not fetch file content from {file_path}"
    
    # Initialize OpenAI client with Groq endpoint
    if not GROQ_API_KEY:
        return "❌ **Error**: GROQ_API_KEY not found in .env file"
    
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )
    
    # Create prompt for documentation generation
    prompt = f"""You are a technical documentation expert. Generate comprehensive markdown documentation for the following code file.

File: {file_path}
Repository: {repo_url}

Code:
```
{content}
```

Generate documentation with the following sections:
1. **Overview**: Brief description of what this file does
2. **Key Components**: List and describe main classes, functions, or modules
3. **Dependencies**: External libraries and imports used
4. **Usage Examples**: How to use the main functionality (if applicable)
5. **Technical Details**: Important implementation details or patterns used

Format the output in clean markdown. Be concise but thorough."""

    try:
        # Call Groq API via OpenAI client
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical documentation expert who creates clear, comprehensive documentation for code files."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",  # Groq model
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=2000
        )
        
        documentation = chat_completion.choices[0].message.content
        
        # Add header with file info
        header = f"""# Documentation: `{file_path}`

**Repository**: {repo_url}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        
        return f"{header}{documentation}"
        
    except Exception as e:
        return f"❌ **Error generating documentation**: {str(e)}"

if __name__ == "__main__":
    # Test the function
    doc = generate_documentation(
        "fastapi/routing.py",
        "https://github.com/tiangolo/fastapi"
    )
    print(doc)
