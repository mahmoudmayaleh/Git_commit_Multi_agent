"""Setup configuration for Git Commit Multi-Agent."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
with open("requirements.txt") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            # Skip the ollama installation note
            if not line.startswith("ollama"):
                requirements.append(line)

setup(
    name="git-commit-agent",
    version="1.0.0",
    author="Mahmoud Mayaleh",
    author_email="",
    description="AI-powered Git commit message generator using Ollama and OpenChat",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mahmoudmayaleh/Git_commit_Multi_agent",
    packages=find_packages(include=["src", "src.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "git-commit-ai=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [".env.example"],
    },
    keywords="git commit ai ollama openai llm automation",
    project_urls={
        "Bug Reports": "https://github.com/mahmoudmayaleh/Git_commit_Multi_agent/issues",
        "Source": "https://github.com/mahmoudmayaleh/Git_commit_Multi_agent",
    },
)
