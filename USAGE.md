# Usage Guide

Complete guide to using the Git Commit Writer Pipeline.

## Quick Start

```powershell
# 1. Setup
pip install -r requirements.txt
copy .env.example .env
# Edit .env with your settings

# 2. Stage changes
git add .

# 3. Generate commit message
python main.py
```

## Detailed Usage

### 1. Basic Usage

Generate a commit message for staged changes:

```powershell
python main.py
```

This will:

1. Analyze your staged changes
2. Generate bullet points describing changes
3. Create a summary
4. Produce a conventional commit message
5. Ask if you want to commit

### 2. Command-Line Options

#### Dry Run (No Commit)

Generate the message without committing:

```powershell
python main.py --dry-run
```

#### Verbose Output

See detailed logs from each agent:

```powershell
python main.py --verbose
```

#### Debug Mode

See all intermediate outputs:

```powershell
python main.py --debug
```

#### Auto Commit

Skip confirmation and commit automatically:

```powershell
python main.py --auto-commit
```

**Warning**: Use with caution! Review generated messages before auto-committing.

#### Save to File

Save the commit message to a file:

```powershell
python main.py --output commit.txt
```

#### Specify Repository

Work with a different repository:

```powershell
python main.py --repo-path "C:\path\to\repo"
```

#### Combined Options

```powershell
python main.py --verbose --dry-run --output message.txt
```

### 3. Programmatic Usage

Use the pipeline in your own scripts:

```python
from pipeline import CommitPipeline

# Create pipeline
pipeline = CommitPipeline(repo_path=".", debug=True)

# Run pipeline
state = pipeline.run()

# Access results
if not state.has_errors():
    print(f"Commit message: {state.commit_message}")
    print(f"Summary: {state.summary}")
    print(f"Changes: {state.bullet_points}")
```

### 4. Using Individual Agents

Work with agents separately:

```python
from state import PipelineState
from llm_client import LLMClient
from agents import DiffAgent, SummaryAgent, CommitWriterAgent

# Initialize
llm_client = LLMClient()
state = PipelineState()

# Run each agent
diff_agent = DiffAgent(repo_path=".")
state = diff_agent.process(state)

summary_agent = SummaryAgent(llm_client)
state = summary_agent.process(state)

commit_agent = CommitWriterAgent(llm_client)
state = commit_agent.process(state)

print(state.commit_message)
```

## Configuration

### Environment Variables

Edit `.env` to configure the pipeline:

```env
# LLM Mode: "local" or "api"
LLM_MODE=local

# For local inference
LOCAL_MODEL_PATH=openchat/openchat-3.5-0106
DEVICE=cuda
USE_8BIT=false

# For API inference
API_BASE_URL=http://localhost:8000/v1
API_KEY=your-key-here

# Pipeline settings
DEBUG_MODE=false
COMMIT_STYLE=conventional
```

### Commit Styles

#### Conventional Commits (Default)

```
feat(api): add user authentication endpoint

- Implement JWT token generation
- Add password hashing with bcrypt
- Create login and logout routes
```

Format: `<type>(<scope>): <description>`

Types:

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (no logic change)
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `test` - Tests
- `build` - Build system
- `ci` - CI/CD
- `chore` - Maintenance

#### Angular Style

```
feat(users): implement user registration

Add new user registration endpoint with email validation
and password strength requirements.

Closes #123
```

#### Custom Templates

Modify `agents/commit_writer_agent.py` to create custom formats.

## Advanced Features

### 1. Custom LLM Parameters

Adjust in `.env`:

```env
MAX_NEW_TOKENS=512      # Max response length
TEMPERATURE=0.7          # Creativity (0.0-1.0)
TOP_P=0.9               # Nucleus sampling
```

### 2. Using Different Models

For local inference, change the model:

```env
LOCAL_MODEL_PATH=meta-llama/Llama-2-7b-chat-hf
```

**Note**: Prompt format may need adjustment for different models.

### 3. API Server Setup

Run your own inference server:

```powershell
# Using vLLM (recommended)
pip install vllm
vllm serve openchat/openchat-3.5-0106 --port 8000

# Using text-generation-inference
docker run -p 8000:80 ghcr.io/huggingface/text-generation-inference:latest --model-id openchat/openchat-3.5-0106
```

Update `.env`:

```env
LLM_MODE=api
API_BASE_URL=http://localhost:8000/v1
```

### 4. Batch Processing

Process multiple repositories:

```python
from pipeline import CommitPipeline

repos = ["repo1", "repo2", "repo3"]

for repo in repos:
    pipeline = CommitPipeline(repo_path=repo)
    state = pipeline.run()

    if not state.has_errors():
        print(f"{repo}: {state.commit_message}")
```

### 5. Custom Agent Logic

Extend agents for custom behavior:

```python
from agents import SummaryAgent

class CustomSummaryAgent(SummaryAgent):
    def _filter_bullet_points(self, bullets):
        # Custom filtering logic
        return [b for b in bullets if "important" in b.lower()]

# Use custom agent
pipeline.summary_agent = CustomSummaryAgent(llm_client)
```

## Workflow Examples

### Example 1: Feature Development

```powershell
# Make changes
# ... edit files ...

# Stage changes
git add src/features/auth.py tests/test_auth.py

# Generate commit
python main.py --verbose

# Review and commit
# Output: "feat(auth): implement user authentication system"
```

### Example 2: Bug Fix

```powershell
# Fix bug
# ... edit files ...

# Stage changes
git add src/api/routes.py

# Generate commit
python main.py

# Output: "fix(api): resolve null pointer in user endpoint"
```

### Example 3: Refactoring

```powershell
# Refactor code
# ... restructure files ...

# Stage changes
git add src/

# Generate commit with debug
python main.py --debug

# Review bullet points and summary before committing
```

### Example 4: Documentation

```powershell
# Update docs
# ... edit README.md ...

# Stage and commit
git add README.md
python main.py --auto-commit

# Output: "docs: update installation instructions"
```

## Best Practices

### 1. Stage Related Changes Together

Group related changes in a single commit:

```powershell
# Good: Feature with tests
git add src/feature.py tests/test_feature.py
python main.py

# Avoid: Unrelated changes
git add file1.py file2.py unrelated.py  # Don't do this
```

### 2. Review Before Committing

Always review the generated message:

```powershell
python main.py --dry-run
# Review output
# If good, run again without --dry-run
```

### 3. Use Verbose Mode for Large Changes

For complex changesets:

```powershell
python main.py --verbose
# Review bullet points and summary
```

### 4. Save Important Messages

Keep a record of commit messages:

```powershell
python main.py --output commits.log
```

### 5. Test Configuration First

Use the example script to test your setup:

```powershell
python tests/example_usage.py
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

### Quick Checks

```powershell
# Verify setup
python quickstart.py

# Test LLM connection
python -c "from llm_client import LLMClient; print(LLMClient().is_available())"

# Check staged changes
git diff --staged

# Validate config
python -c "from config import Config; Config.validate()"
```

## Tips and Tricks

### 1. Faster Iteration with API Mode

For development, use API mode for faster response times:

```env
LLM_MODE=api
```

### 2. Customize for Your Team

Adjust commit style to match your team's conventions:

```env
COMMIT_STYLE=angular  # or conventional, gitmoji
```

### 3. Pre-commit Hook

Integrate with Git hooks:

```bash
# .git/hooks/prepare-commit-msg
#!/bin/sh
python main.py --dry-run --output .git/COMMIT_EDITMSG
```

### 4. Alias for Quick Access

Add to your PowerShell profile:

```powershell
function gcai { python C:\path\to\code\main.py $args }

# Usage:
gcai --verbose
gcai --dry-run
```

### 5. Use with Pre-commit

Install [pre-commit](https://pre-commit.com/) framework and add:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ai-commit-msg
        name: AI Commit Message
        entry: python main.py --dry-run
        language: system
        always_run: true
```

## Next Steps

- Read [README.md](README.md) for overview
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for issues
- Run `python tests/example_usage.py` for hands-on demo
- Customize agents in `agents/` directory
- Experiment with different LLM parameters

---

**Happy committing! 🚀**
