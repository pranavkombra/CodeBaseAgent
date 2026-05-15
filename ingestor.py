import requests
from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_github_repo(repo_url):
    parts = repo_url.strip("/").split("/")
    owner = parts[-2]
    repo = parts[-1]
    
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
    response = requests.get(api_url, headers=headers)
    tree = response.json().get("tree", [])
    
    files = []
    for item in tree:
        if (item["type"] == "blob" and
            item["path"].endswith(".py") and
            not item["path"].startswith("tests/") and
            not item["path"].startswith("docs/") and
            not item["path"].startswith("docs_src/")):
            
            file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{item['path']}"
            content = requests.get(file_url, headers=headers).text
            files.append({
                "path": item["path"],
                "content": content
            })
    
    return files

if __name__ == "__main__":
    files = fetch_github_repo("https://github.com/tiangolo/fastapi")
    print(f"Total files fetched: {len(files)}")
    for f in files[:5]:
        print(f["path"])
        