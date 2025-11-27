# Project Structure Overview

This document provides a complete overview of the Git Commit Writer Pipeline project structure.

## Directory Structure

```
code/
├── agents/                      # Agent implementations
│   ├── __init__.py             # Package initialization
│   ├── base_agent.py           # Abstract base agent class
│   ├── diff_agent.py           # Git diff parser agent
│   ├── summary_agent.py        # Change summarizer agent
│   └── commit_writer_agent.py  # Commit message generator agent
│
├── tests/                       # Test suite and examples
│   ├── __init__.py             # Package initialization
│   ├── test_state.py           # Unit tests for state management
│   └── example_usage.py        # Example usage demonstrations
│
├── config.py                    # Configuration management
├── llm_client.py               # LLM client (local & API)
├── main.py                      # Main CLI application
├── pipeline.py                  # Pipeline orchestrator
├── state.py                     # State management classes
├── quickstart.py               # Setup verification script
│
├── .env.example                 # Example environment configuration
├── .gitignore                   # Git ignore patterns
├── requirements.txt             # Python dependencies
├── README.md                    # Project overview and setup
├── USAGE.md                     # Detailed usage guide
└── TROUBLESHOOTING.md          # Troubleshooting guide
```

## Core Components

### 1. State Management (`state.py`)

**Purpose**: Manages data flow between agents

**Classes**:

- `PipelineState`: Central state object containing:

  - `staged_diff`: Raw Git diff output
  - `bullet_points`: Parsed change descriptions
  - `summary`: Concise summary of changes
  - `commit_message`: Final commit message
  - `errors`: Error tracking
  - `metadata`: Additional information

- `StateValidator`: Validates state at different pipeline stages

**Key Features**:

- Serialization to/from dict/JSON
- Error tracking
- Stage validation
- Metadata management

### 2. LLM Client (`llm_client.py`)

**Purpose**: Unified interface for OpenChat-3.5 inference

**Classes**:

- `LLMConfig`: Configuration dataclass
- `BaseLLMClient`: Abstract base class
- `LocalLLMClient`: Local inference using Transformers
- `APILLMClient`: API-based inference
- `LLMClient`: Main unified client

**Key Features**:

- Auto-selection between local/API modes
- Proper prompt formatting for OpenChat-3.5
- 8-bit quantization support
- Error handling and retries
- GPU/CPU support

### 3. Agents (`agents/`)

#### Base Agent (`base_agent.py`)

**Purpose**: Abstract interface for all agents

**Features**:

- Common logging interface
- Input validation
- Error handling
- Stage tracking

#### DiffAgent (`diff_agent.py`)

**Purpose**: Parse Git diffs into structured bullet points

**Process**:

1. Execute `git diff --staged`
2. Parse diff by file
3. Detect change types (add/modify/delete/rename)
4. Extract function/class changes
5. Generate human-readable bullet points

**Features**:

- Rule-based parsing (no LLM required)
- Optional LLM-enhanced parsing
- Detailed change detection
- File statistics tracking

#### SummaryAgent (`summary_agent.py`)

**Purpose**: Summarize bullet points into concise context

**Process**:

1. Filter noise from bullet points
2. Group changes by category (features/fixes/refactoring/etc.)
3. Generate natural language summary using LLM
4. Fallback to rule-based summary if needed

**Features**:

- Smart filtering (removes whitespace changes, typos, etc.)
- Categorization (feat/fix/refactor/etc.)
- Configurable summary length
- LLM-powered summarization

#### CommitWriterAgent (`commit_writer_agent.py`)

**Purpose**: Transform summary into conventional commit message

**Process**:

1. Infer commit type from summary
2. Generate commit message using LLM
3. Validate conventional format
4. Auto-fix malformed messages

**Features**:

- Conventional Commits format
- Type inference (feat/fix/docs/etc.)
- Format validation and correction
- Multiple commit styles supported

### 4. Pipeline (`pipeline.py`)

**Purpose**: Orchestrate all agents in sequence

**Class**: `CommitPipeline`

**Process**:

1. Initialize agents with shared LLM client
2. Run DiffAgent
3. Run SummaryAgent
4. Run CommitWriterAgent
5. Validate final output

**Features**:

- Sequential agent execution
- Error handling and recovery
- Debug output
- Repository validation

### 5. Configuration (`config.py`)

**Purpose**: Load and validate configuration from environment

**Class**: `Config`

**Settings**:

- LLM configuration (mode, model, device, etc.)
- API configuration (URL, key, model)
- Pipeline configuration (debug, style, etc.)
- Git configuration (repo path)

**Features**:

- Environment variable loading
- Configuration validation
- Display current config

### 6. Main CLI (`main.py`)

**Purpose**: Command-line interface for the pipeline

**Features**:

- Argument parsing
- Colored output (with colorama)
- Interactive prompts
- Dry-run mode
- Verbose/debug modes
- Auto-commit option
- File output

**Usage**:

```powershell
python main.py [--dry-run] [--verbose] [--auto-commit] [--output FILE]
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Git Repository                          │
│                      (Staged Changes)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  DiffAgent    │
                    └───────┬───────┘
                            │ staged_diff
                            │ bullet_points
                            ▼
                    ┌───────────────┐
                    │ SummaryAgent  │
                    └───────┬───────┘
                            │ summary
                            ▼
                    ┌───────────────┐
                    │ CommitWriter  │
                    └───────┬───────┘
                            │ commit_message
                            ▼
                    ┌───────────────┐
                    │  Git Commit   │
                    └───────────────┘
```

## Configuration Flow

```
.env file
    │
    ▼
Config.from_env()
    │
    ├──► LLMConfig ──► LLMClient ──► Agents
    │
    └──► Pipeline Configuration
```

## Agent Communication

All agents communicate via the shared `PipelineState` object:

```python
state = PipelineState()

# DiffAgent populates staged_diff and bullet_points
state = diff_agent.process(state)

# SummaryAgent reads bullet_points, produces summary
state = summary_agent.process(state)

# CommitWriterAgent reads summary, produces commit_message
state = commit_writer_agent.process(state)

# Final result in state.commit_message
```

## Error Handling

Errors are tracked at multiple levels:

1. **Agent Level**: Each agent catches exceptions and adds to `state.errors`
2. **Pipeline Level**: Pipeline checks for errors after each agent
3. **Main Level**: CLI handles final errors and displays to user

```python
try:
    state = agent.process(state)
except Exception as e:
    state.add_error(str(e), agent.name)
    logger.error(f"Agent failed: {e}")
```

## Testing

### Unit Tests (`tests/test_state.py`)

Tests for state management:

- State initialization
- Error tracking
- Validation
- Serialization

Run with:

```powershell
pytest tests/test_state.py -v
```

### Example Usage (`tests/example_usage.py`)

Interactive demonstrations:

- Complete pipeline with test repository
- Individual agent usage
- Programmatic API examples

Run with:

```powershell
python tests/example_usage.py
```

## Extension Points

The pipeline is designed for easy customization:

### 1. Custom Agents

Extend `BaseAgent`:

```python
from agents.base_agent import BaseAgent
from state import PipelineState

class CustomAgent(BaseAgent):
    def process(self, state: PipelineState) -> PipelineState:
        # Your custom logic
        return state
```

### 2. Custom LLM Clients

Implement `BaseLLMClient`:

```python
from llm_client import BaseLLMClient

class CustomLLMClient(BaseLLMClient):
    def generate(self, prompt: str, **kwargs) -> str:
        # Your custom LLM logic
        pass

    def is_available(self) -> bool:
        return True
```

### 3. Custom Commit Styles

Modify `CommitWriterAgent._create_prompt()`:

```python
def _create_prompt(self, context: str) -> str:
    if self.commit_style == "my_custom_style":
        return f"Custom prompt for {context}"
    # ... existing logic
```

## Performance Considerations

### Memory Usage

- **Local Inference**: ~7GB GPU VRAM or ~14GB RAM
- **8-bit Quantization**: ~4GB GPU VRAM
- **API Mode**: Minimal (<1GB)

### Speed

- **Local (GPU)**: ~5-10 seconds per commit
- **Local (CPU)**: ~30-60 seconds per commit
- **API (vLLM)**: ~2-5 seconds per commit

### Optimization Tips

1. Use API mode for development
2. Enable 8-bit quantization for memory savings
3. Use GPU when available
4. Reduce MAX_NEW_TOKENS for faster generation

## Security Considerations

1. **API Keys**: Never commit .env file
2. **Code Review**: Always review generated messages
3. **Sensitive Data**: Pipeline sends diffs to LLM (local/API)
4. **Git Hooks**: Use with caution in automated workflows

## Dependencies

### Core

- GitPython: Git integration
- python-dotenv: Environment configuration
- requests: API communication

### LLM (Local)

- torch: Deep learning framework
- transformers: Model loading and inference
- accelerate: Optimization utilities

### Optional

- colorama: Colored terminal output
- pytest: Testing framework
- vllm: Fast API inference server

## Future Enhancements

Potential areas for improvement:

1. **Multi-model support**: Easy switching between LLMs
2. **Commit templates**: User-defined templates
3. **Interactive editing**: Edit generated messages before committing
4. **History learning**: Learn from past commits
5. **Team style learning**: Adapt to team conventions
6. **Webhook integration**: Integrate with CI/CD
7. **GUI**: Web or desktop interface
8. **Caching**: Cache similar diffs for speed

---

**Last Updated**: November 2025
**Version**: 1.0.0
