# API Reference

Complete API documentation for the Git Commit Writer Pipeline.

## Quick Links

- [Pipeline](#pipeline-api)
- [Agents](#agents-api)
- [State](#state-api)
- [LLM Client](#llm-client-api)
- [Configuration](#configuration-api)

---

## Pipeline API

### `CommitPipeline`

Main pipeline orchestrator.

```python
class CommitPipeline:
    def __init__(
        self,
        repo_path: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        debug: bool = False
    )
```

**Parameters:**

- `repo_path`: Path to Git repository (default: current directory)
- `llm_client`: Custom LLM client (default: creates from config)
- `debug`: Enable debug output (default: False)

**Methods:**

#### `run(state: Optional[PipelineState] = None) -> PipelineState`

Run the complete pipeline.

```python
pipeline = CommitPipeline()
state = pipeline.run()
```

**Returns:** `PipelineState` with commit message

#### `get_commit_message() -> Optional[str]`

Run pipeline and return only the commit message.

```python
message = pipeline.get_commit_message()
```

**Returns:** Commit message string or None

#### `validate_repository() -> bool`

Check if repository has staged changes.

```python
is_valid = pipeline.validate_repository()
```

**Returns:** True if valid

### Helper Function

#### `create_pipeline(repo_path: Optional[str] = None, debug: bool = False) -> CommitPipeline`

Convenience function to create a pipeline.

```python
from pipeline import create_pipeline

pipeline = create_pipeline(debug=True)
```

---

## Agents API

### Base Agent

All agents inherit from `BaseAgent`.

```python
class BaseAgent(ABC):
    def __init__(self, name: Optional[str] = None)

    @abstractmethod
    def process(self, state: PipelineState) -> PipelineState:
        pass
```

### DiffAgent

Parses Git diffs into bullet points.

```python
class DiffAgent(BaseAgent):
    def __init__(
        self,
        repo_path: str = ".",
        use_llm: bool = False,
        llm_client: Optional[LLMClient] = None
    )
```

**Parameters:**

- `repo_path`: Repository path
- `use_llm`: Use LLM for enhanced parsing
- `llm_client`: LLM client for parsing

**Example:**

```python
from agents import DiffAgent
from state import PipelineState

agent = DiffAgent(repo_path=".", use_llm=False)
state = PipelineState()
state = agent.process(state)

print(state.bullet_points)
```

### SummaryAgent

Summarizes bullet points.

```python
class SummaryAgent(BaseAgent):
    def __init__(
        self,
        llm_client: LLMClient,
        max_summary_length: int = 500
    )
```

**Parameters:**

- `llm_client`: LLM client (required)
- `max_summary_length`: Max chars in summary

**Example:**

```python
from agents import SummaryAgent
from llm_client import LLMClient

llm = LLMClient()
agent = SummaryAgent(llm, max_summary_length=300)
state = agent.process(state)

print(state.summary)
```

### CommitWriterAgent

Generates commit messages.

```python
class CommitWriterAgent(BaseAgent):
    def __init__(
        self,
        llm_client: LLMClient,
        commit_style: str = "conventional"
    )
```

**Parameters:**

- `llm_client`: LLM client (required)
- `commit_style`: "conventional", "angular", or "gitmoji"

**Example:**

```python
from agents import CommitWriterAgent

agent = CommitWriterAgent(llm, commit_style="conventional")
state = agent.process(state)

print(state.commit_message)
```

---

## State API

### PipelineState

Central state object.

```python
@dataclass
class PipelineState:
    staged_diff: Optional[str] = None
    bullet_points: Optional[List[str]] = None
    summary: Optional[str] = None
    commit_message: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Methods:**

#### `add_error(error: str, agent: str = "Unknown") -> None`

Add an error to the state.

```python
state.add_error("Something went wrong", "MyAgent")
```

#### `has_errors() -> bool`

Check if state has errors.

```python
if state.has_errors():
    print("Errors:", state.errors)
```

#### `is_ready_for_agent(agent_name: str) -> bool`

Check if state is ready for an agent.

```python
if state.is_ready_for_agent("SummaryAgent"):
    # Process
    pass
```

#### `get_stage_output(stage: str) -> Optional[Any]`

Get output from a specific stage.

```python
bullets = state.get_stage_output("bullet_points")
```

#### `to_dict() -> Dict[str, Any]`

Convert to dictionary.

```python
state_dict = state.to_dict()
```

#### `to_json(indent: int = 2) -> str`

Convert to JSON string.

```python
json_str = state.to_json()
```

#### `from_dict(data: Dict[str, Any]) -> PipelineState`

Create from dictionary.

```python
state = PipelineState.from_dict(data)
```

### StateValidator

Validates pipeline state.

```python
class StateValidator:
    @staticmethod
    def validate_diff(state: PipelineState) -> bool

    @staticmethod
    def validate_bullet_points(state: PipelineState) -> bool

    @staticmethod
    def validate_summary(state: PipelineState) -> bool

    @staticmethod
    def validate_commit_message(state: PipelineState) -> bool
```

**Example:**

```python
from state import StateValidator

if StateValidator.validate_diff(state):
    print("Diff is valid")
```

---

## LLM Client API

### LLMConfig

Configuration for LLM client.

```python
@dataclass
class LLMConfig:
    mode: str = "local"
    model_path: str = "openchat/openchat-3.5-0106"
    device: str = "cuda"
    max_new_tokens: int = 512
    temperature: float = 0.7
    api_base_url: str = "http://localhost:8000/v1"
    api_key: str = ""
    api_model: str = "openchat-3.5"
    use_8bit: bool = False
    top_p: float = 0.9
```

**Methods:**

#### `from_env() -> LLMConfig`

Create config from environment variables.

```python
config = LLMConfig.from_env()
```

### LLMClient

Unified LLM client.

```python
class LLMClient:
    def __init__(self, config: Optional[LLMConfig] = None)
```

**Methods:**

#### `generate(prompt: str, **kwargs) -> str`

Generate text from prompt.

```python
llm = LLMClient()
response = llm.generate(
    "Your prompt here",
    max_new_tokens=256,
    temperature=0.5
)
```

**Parameters:**

- `prompt`: Input prompt
- `max_new_tokens`: Max tokens to generate (optional)
- `temperature`: Sampling temperature (optional)
- `top_p`: Nucleus sampling parameter (optional)

**Returns:** Generated text

#### `is_available() -> bool`

Check if LLM is available.

```python
if llm.is_available():
    response = llm.generate("prompt")
```

### Helper Function

#### `create_llm_client(mode: Optional[str] = None) -> LLMClient`

Create LLM client with optional mode override.

```python
from llm_client import create_llm_client

llm = create_llm_client(mode="local")
```

---

## Configuration API

### Config

Application configuration.

```python
class Config:
    # LLM Configuration
    LLM_MODE: str
    LOCAL_MODEL_PATH: str
    DEVICE: str
    MAX_NEW_TOKENS: int
    TEMPERATURE: float

    # API Configuration
    API_BASE_URL: str
    API_KEY: str
    API_MODEL: str

    # Git Configuration
    GIT_REPO_PATH: str

    # Pipeline Configuration
    DEBUG_MODE: bool
    LOG_LEVEL: str
    COMMIT_STYLE: str
    USE_8BIT: bool
    USE_LLM_FOR_DIFF: bool
```

**Methods:**

#### `validate() -> bool`

Validate configuration.

```python
if Config.validate():
    print("Configuration is valid")
```

#### `display() -> None`

Display current configuration.

```python
Config.display()
```

---

## Usage Examples

### Example 1: Basic Pipeline

```python
from pipeline import CommitPipeline

pipeline = CommitPipeline()
state = pipeline.run()

if not state.has_errors():
    print(f"Commit: {state.commit_message}")
```

### Example 2: Custom Configuration

```python
from pipeline import CommitPipeline
from llm_client import LLMClient, LLMConfig

config = LLMConfig(
    mode="local",
    device="cpu",
    temperature=0.5
)

llm = LLMClient(config)
pipeline = CommitPipeline(llm_client=llm, debug=True)

state = pipeline.run()
```

### Example 3: Individual Agents

```python
from state import PipelineState
from llm_client import LLMClient
from agents import DiffAgent, SummaryAgent, CommitWriterAgent

# Setup
llm = LLMClient()
state = PipelineState()

# Run agents
diff_agent = DiffAgent()
state = diff_agent.process(state)

summary_agent = SummaryAgent(llm)
state = summary_agent.process(state)

commit_agent = CommitWriterAgent(llm)
state = commit_agent.process(state)

print(state.commit_message)
```

### Example 4: Custom Agent

```python
from agents.base_agent import BaseAgent
from state import PipelineState

class CustomAgent(BaseAgent):
    def process(self, state: PipelineState) -> PipelineState:
        # Your custom logic
        state.metadata["custom_data"] = "value"
        return state

# Use it
agent = CustomAgent()
state = agent.process(state)
```

### Example 5: Error Handling

```python
from pipeline import CommitPipeline

pipeline = CommitPipeline()
state = pipeline.run()

if state.has_errors():
    print("Errors occurred:")
    for error in state.errors:
        print(f"  - {error}")
else:
    print(f"Success: {state.commit_message}")
```

### Example 6: Serialization

```python
from state import PipelineState
import json

# Create state
state = PipelineState()
state.summary = "Test summary"
state.commit_message = "feat: test commit"

# Save to file
with open("state.json", "w") as f:
    f.write(state.to_json())

# Load from file
with open("state.json", "r") as f:
    data = json.load(f)
    loaded_state = PipelineState.from_dict(data)
```

---

## Type Definitions

```python
from typing import Optional, List, Dict, Any

# State types
StateDict = Dict[str, Any]
BulletPoints = List[str]
Errors = List[str]

# LLM types
Prompt = str
Response = str
GenerationParams = Dict[str, Any]

# Agent types
AgentName = str
StageName = str
```

---

## Constants

```python
# Commit types
COMMIT_TYPES = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "build": "Changes that affect the build system or external dependencies",
    "ci": "Changes to CI configuration files and scripts",
    "chore": "Other changes that don't modify src or test files",
    "revert": "Reverts a previous commit"
}

# Agent names
DIFF_AGENT = "DiffAgent"
SUMMARY_AGENT = "SummaryAgent"
COMMIT_WRITER_AGENT = "CommitWriterAgent"

# Commit styles
COMMIT_STYLES = ["conventional", "angular", "gitmoji"]

# LLM modes
LLM_MODES = ["local", "api"]
```

---

## Exceptions

The pipeline uses standard Python exceptions:

- `ValueError`: Invalid configuration or parameters
- `RuntimeError`: Runtime errors (e.g., model not initialized)
- `GitCommandError`: Git operations failed
- `requests.exceptions.RequestException`: API errors

All exceptions are caught and added to `state.errors`.

---

## Best Practices

### 1. Always Check for Errors

```python
state = pipeline.run()
if state.has_errors():
    # Handle errors
    pass
```

### 2. Use Type Hints

```python
def process_commit(state: PipelineState) -> str:
    return state.commit_message or "No message"
```

### 3. Validate Input

```python
if not StateValidator.validate_diff(state):
    print("Invalid diff")
```

### 4. Use Context Managers for Resources

```python
from llm_client import LLMClient

llm = LLMClient()
try:
    response = llm.generate("prompt")
finally:
    # Cleanup if needed
    pass
```

### 5. Configure via Environment

```python
# Use .env file instead of hardcoding
from config import Config
Config.display()
```

---

## Version History

### v1.0.0 (2025-11-26)

- Initial release
- Three-agent architecture
- OpenChat-3.5 integration
- Local and API modes
- Comprehensive documentation

---

**For more information, see:**

- [README.md](README.md) - Project overview
- [USAGE.md](USAGE.md) - Usage guide
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Technical details
