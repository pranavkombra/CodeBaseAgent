import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def extract_functions(file_content):
    functions = []
    lines = file_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('def '):
            func_name = line.split('def ')[1].split('(')[0]
            func_lines = [line]
            i += 1
            while i < len(lines):
                if lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t'):
                    break
                func_lines.append(lines[i])
                i += 1
            functions.append((func_name, '\n'.join(func_lines)))
        else:
            i += 1
    return functions

def generate_tests(function_name, function_code):
    # Truncate long functions
    if len(function_code) > 3000:
        function_code = function_code[:3000] + "\n# ... (code truncated due to length)"
    
    prompt = f"Write pytest tests for: {function_name}\n\nCode:\n{function_code}\n\nReturn only Python code."
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Smaller model = lower token usage
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500  # Limit response size
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"# Error: {str(e)}"

def save_tests_to_file(test_code, original_file_path):
    test_path = f"test_{os.path.basename(original_file_path)}"
    with open(test_path, 'w') as f:
        f.write("import pytest\n\n")
        f.write(test_code)
    return test_path