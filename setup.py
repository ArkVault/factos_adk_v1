from setuptools import setup, find_packages
import os

# Leer README.md si existe
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "AI-powered fact-checking agents using Google ADK"

setup(
    name="factos-agents",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "google-adk==1.4.2",
        "firecrawl-py==2.9.0",
        "pytest",
        "python-dotenv",
        "deprecated",
        "aiohttp",
        "beautifulsoup4",
        "fastapi",
        "uvicorn",
        "pydantic",
        "fuzzywuzzy",
    ],
    python_requires=">=3.12",
    author="Factos Team",
    description="AI-powered fact-checking agents using Google ADK",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
)
