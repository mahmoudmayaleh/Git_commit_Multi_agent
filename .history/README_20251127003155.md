# 🤖 Git Commit AI - Three-Agent Commit Message Generator

An intelligent, fully automated pipeline that generates high-quality conventional Git commit messages from code diffs using a multi-agent system powered by **OpenChat 7B** running locally via **Ollama**.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Pipeline Flow](#pipeline-flow)
- [Customization](#customization)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This pipeline leverages **Ollama** (free, open-source LLM runtime) with **OpenChat 7B** to automatically generate professional commit messages. It consists of three specialized agents that work sequentially:

1. **DiffAgent** - Parses `git diff --staged` and extracts structured change information
2. **SummaryAgent** - Filters and summarizes changes using LLM into concise context
3. **CommitWriterAgent** - Crafts conventional commit messages following best practices

**Why Ollama?**

- ✅ 100% Free & Open Source
- ✅ Privacy-focused (runs locally)
- ✅ Optimized for CPU/GPU inference
- ✅ Easy model management
- ✅ No API costs or rate limits

## 🏗️ Architecture

```
┌─────────────────┐
│   Staged Code   │
└────────┬────────┘
         │ git diff --staged
         ▼
┌─────────────────┐
│   DiffAgent     │ Parses diffs → Bullet points
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SummaryAgent   │ Filters/groups → Summary
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CommitWriter    │ Formats → Commit message
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Final Message   │
└─────────────────┘
```

### State Management

All agents share a central `PipelineState` object:

```python
{
    "staged_diff": str,           # Raw git diff output
    "bullet_points": List[str],   # Parsed changes
    "summary": str,               # Concise summary
    "commit_message": str,        # Final output
    "errors": List[str]           # Error tracking
}
```

## 🚀 Installation

### Prerequisites

- **Python 3.8+** - Required for running the pipeline
- **Git** - Version control system
- **Ollama** - Local LLM runtime ([Download here](https://ollama.com))
- **8GB+ RAM** - Recommended for smooth inference

### Step 1: Install Ollama

**Windows:**

```powershell
# Download from https://ollama.com/download
# Run the installer (OllamaSetup.exe)
# Ollama runs automatically as a service
```

**macOS:**

```bash
# Download from https://ollama.com/download
# Or use Homebrew:
brew install ollama
```

**Linux:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Pull OpenChat Model

```powershell
# Download OpenChat 7B model (~4.1GB)
ollama pull openchat:7b

# Verify installation
ollama list
# Should show: openchat:7b
```

### Step 3: Install Python Dependencies

```powershell
cd c:\Users\Hp\Downloads\GenAI\code
pip install -r requirements.txt
```

**Required packages:**

- GitPython (Git integration)
- python-dotenv (Configuration)
- requests (Ollama API communication)
- colorama (Colored terminal output)

### Step 4: Configure Environment

```powershell
# Copy example config
copy .env.example .env

# Edit .env if needed (default settings work with Ollama)
```

Default configuration uses Ollama on `http://localhost:11434` with `openchat:7b` model.

## ⚙️ Configuration

The pipeline is configured via the `.env` file. Default settings work out-of-the-box with Ollama.

### Environment Variables

| Variable        | Default                       | Description                           |
| --------------- | ----------------------------- | ------------------------------------- |
| `LLM_MODE`      | `api`                         | Use `api` for Ollama                  |
| `API_BASE_URL`  | `http://localhost:11434/v1`   | Ollama API endpoint                   |
| `API_KEY`       | `ollama`                      | Any value works (Ollama doesn't auth) |
| `API_MODEL`     | `openchat:7b`                 | Model name in Ollama                  |
| `DEBUG_MODE`    | `true`                        | Show intermediate outputs             |
| `LOG_LEVEL`     | `INFO`                        | Logging verbosity                     |
| `COMMIT_STYLE`  | `conventional`                | Commit message format                 |
| `GIT_REPO_PATH` | _(empty = current directory)_ | Target repository path                |

### Using Different Models

You can use any model supported by Ollama:

```powershell
# Try other models
ollama pull llama2:7b
ollama pull codellama:7b
ollama pull mistral:7b

# Update .env
API_MODEL=llama2:7b
```

### Advanced Ollama Settings

```powershell
# Check Ollama status
ollama list

# View running models
ollama ps

# Stop a model to free memory
ollama stop openchat:7b

# Remove a model
ollama rm openchat:7b
```

## 📖 Usage

### Quick Start

```powershell
# 1. Make your code changes
# (edit files, add features, fix bugs)

# 2. Stage changes for commit
git add .

# 3. Generate and apply commit message
python main.py

# That's it! The AI generates the commit message and commits.
```

### Preview Before Committing

```powershell
# See the generated message without committing
python main.py --dry-run
```

Example output:

```
======================================================================
  📝 GENERATED COMMIT MESSAGE
======================================================================

feat(auth): implement user authentication with JWT tokens

- Add login/logout endpoints
- Implement JWT token generation and validation
- Add authentication middleware
- Create user session management
```

### Command-Line Options

```powershell
# Dry run - preview message only
python main.py --dry-run

# Verbose mode - show all agent outputs
python main.py --verbose

# Use specific repository path
python main.py --repo-path C:\path\to\repo

# Output to file instead of committing
python main.py --output commit_msg.txt

# Quiet mode - minimal output
python main.py --quiet
```

### Real-World Examples

**Example 1: Feature Development**

```powershell
# You added a new API endpoint
git add src/api/routes.py src/controllers/user_controller.py
python main.py

# Generated: "feat(api): add user profile retrieval endpoint"
```

**Example 2: Bug Fix**

```powershell
# You fixed a calculation bug
git add src/utils/calculator.py tests/test_calculator.py
python main.py

# Generated: "fix(calculator): correct floating point precision in division"
```

**Example 3: Refactoring**

```powershell
# You reorganized modules
git add src/
python main.py

# Generated: "refactor(core): restructure module organization for better maintainability"
```

### Programmatic Usage

```python
from pipeline import CommitPipeline

# Initialize pipeline
pipeline = CommitPipeline(repo_path=".", debug=True)

# Run all agents
result = pipeline.run()

# Access outputs
print(result.commit_message)
print(result.summary)
print(result.bullet_points)
```

## 🔄 Pipeline Flow

### 1. DiffAgent

```python
Input:  git diff --staged (raw text)
Output: [
    "• Added new function `calculate_total()` in utils/math.py",
    "• Updated API endpoint `/users` in routes/api.py",
    "• Removed deprecated `oldFunction()` from legacy/code.py"
]
```

### 2. SummaryAgent

```python
Input:  Bullet points from DiffAgent
Output: "Implemented new calculation utilities and updated user API
         endpoint. Removed deprecated legacy functions."
```

### 3. CommitWriterAgent

```python
Input:  Summary from SummaryAgent
Output: "feat(api): implement calculation utilities and update user endpoint

- Add calculate_total function for arithmetic operations
- Update /users API endpoint with new response format
- Remove deprecated functions from legacy codebase"
```

## 🎨 Customization

### Custom Commit Templates

Edit `agents/commit_writer_agent.py` to customize the prompt:

```python
COMMIT_TEMPLATE = """
Your custom instructions here...
"""
```

### Adding New Agents

```python
from agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def process(self, state: PipelineState) -> PipelineState:
        # Your logic here
        return state
```

### Using Different LLMs

Modify `llm_client.py` to support other models:

```python
class LLMClient:
    def __init__(self, model_name: str = "your-model"):
        # Custom initialization
        pass
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_diff_agent.py -v
```

### Example Test

```python
python tests/example_usage.py
```

This will:

1. Create a test repository
2. Make sample changes
3. Run the full pipeline
4. Display outputs from each agent

## 🔧 Troubleshooting

### Ollama Connection Issues

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running (Windows):
# Ollama should auto-start as a service
# Check: Services → Ollama

# Manual start:
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

### Model Not Found

```powershell
# List installed models
ollama list

# If openchat:7b is missing:
ollama pull openchat:7b
```

### Timeout Errors

If you see "Read timed out" errors:

```powershell
# Edit .env and increase timeout
# The timeout is hardcoded in llm_client.py as 300 seconds
# For slower machines, edit llm_client.py line ~223:
# response = self.session.post(url, json=payload, timeout=600)
```

### Git Repository Not Found

```powershell
# Ensure you're in a git repository
git init

# Or specify path explicitly
python main.py --repo-path C:\path\to\your\repo
```

### No Staged Changes

```powershell
# Check git status
git status

# Stage files before running
git add <files>

# Or stage all changes
git add .
```

### Memory Issues

```powershell
# Use a smaller model
ollama pull tinyllama

# Update .env
API_MODEL=tinyllama

# Or use llama2:7b-chat which is more efficient
ollama pull llama2:7b-chat
API_MODEL=llama2:7b-chat
```

### Import Errors

```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or install individually
pip install GitPython python-dotenv requests colorama
```

## 📚 Resources

- [Ollama Official Website](https://ollama.com)
- [Ollama GitHub Repository](https://github.com/ollama/ollama)
- [OpenChat Model Card](https://ollama.com/library/openchat)
- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [GitPython Documentation](https://gitpython.readthedocs.io/)

## 🎯 Project Status

**Version:** 1.0.0  
**Status:** Production Ready ✅  
**LLM Backend:** Ollama + OpenChat 7B  
**License:** MIT

## 💡 Tips & Best Practices

1. **Stage related changes together** - Better commit messages when changes are cohesive
2. **Use --dry-run first** - Always preview before committing
3. **Review generated messages** - AI is smart but not perfect
4. **Keep Ollama updated** - `ollama upgrade` for latest features
5. **Use appropriate models** - Smaller models for speed, larger for quality

## 🚀 Future Enhancements

- [ ] Support for commit message templates
- [ ] Integration with GitHub/GitLab APIs
- [ ] Multi-commit suggestions for large changesets
- [ ] VS Code extension
- [ ] Git hook automation
- [ ] Support for more LLM backends

## 📄 License

MIT License - Free to use, modify, and distribute.

## 🤝 Contributing

Contributions welcome! This project demonstrates:

- Multi-agent AI systems
- LLM integration with Ollama
- Git automation
- Clean Python architecture

Feel free to:

1. Fork the repository
2. Add features or fix bugs
3. Submit pull requests
4. Report issues

---

**Built with ❤️ using Ollama, OpenChat, and Python**  
**100% Free • 100% Open Source • 100% Privacy-Focused**
