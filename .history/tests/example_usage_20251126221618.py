"""
Example Usage Script

This script demonstrates how to use the pipeline programmatically
and creates a test repository to show the full workflow.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from git import Repo
from pipeline import CommitPipeline
from state import PipelineState
from config import Config


def create_test_repository():
    """
    Create a test Git repository with sample changes.
    
    Returns:
        Path to test repository
    """
    # Create temporary directory
    test_dir = tempfile.mkdtemp(prefix="git_commit_test_")
    print(f"Created test repository at: {test_dir}")
    
    # Initialize Git repo
    repo = Repo.init(test_dir)
    
    # Create initial file
    initial_file = Path(test_dir) / "hello.py"
    initial_file.write_text("""def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")
    
    # Initial commit
    repo.index.add(["hello.py"])
    repo.index.commit("Initial commit")
    
    print("✓ Created initial commit")
    
    # Make some changes
    # 1. Add a new function
    initial_file.write_text("""def hello():
    print("Hello, World!")

def greet(name):
    \"\"\"Greet a person by name.\"\"\"
    print(f"Hello, {name}!")

def calculate_sum(a, b):
    \"\"\"Calculate the sum of two numbers.\"\"\"
    return a + b

if __name__ == "__main__":
    hello()
    greet("Alice")
    print(f"Sum: {calculate_sum(5, 3)}")
""")
    
    # 2. Add a new file
    new_file = Path(test_dir) / "utils.py"
    new_file.write_text("""\"\"\"Utility functions.\"\"\"

def validate_email(email):
    \"\"\"Validate email format.\"\"\"
    return "@" in email and "." in email

def format_name(first_name, last_name):
    \"\"\"Format full name.\"\"\"
    return f"{first_name} {last_name}".title()
""")
    
    # 3. Add a config file
    config_file = Path(test_dir) / "config.json"
    config_file.write_text("""{
    "app_name": "Test App",
    "version": "1.0.0",
    "debug": true
}
""")
    
    # Stage all changes
    repo.index.add(["hello.py", "utils.py", "config.json"])
    
    print("✓ Staged test changes:")
    print("  - Modified hello.py (added 2 new functions)")
    print("  - Added utils.py (new utility module)")
    print("  - Added config.json (configuration file)")
    
    return test_dir, repo


def demonstrate_pipeline():
    """Demonstrate the complete pipeline workflow."""
    print("\n" + "="*70)
    print("  Git Commit Writer Pipeline - Example Usage")
    print("="*70 + "\n")
    
    # Create test repository
    test_repo_path, repo = create_test_repository()
    
    try:
        # Initialize pipeline
        print("\n" + "-"*70)
        print("STEP 1: Initialize Pipeline")
        print("-"*70)
        
        pipeline = CommitPipeline(
            repo_path=test_repo_path,
            debug=True
        )
        
        print("✓ Pipeline initialized")
        
        # Run pipeline
        print("\n" + "-"*70)
        print("STEP 2: Run Pipeline")
        print("-"*70 + "\n")
        
        state = pipeline.run()
        
        # Display results
        print("\n" + "-"*70)
        print("STEP 3: Results")
        print("-"*70 + "\n")
        
        if state.has_errors():
            print("❌ Pipeline failed with errors:")
            for error in state.errors:
                print(f"  • {error}")
            return
        
        print("📊 BULLET POINTS:")
        for bullet in state.bullet_points or []:
            print(f"  {bullet}")
        
        print(f"\n📝 SUMMARY:")
        print(f"  {state.summary}")
        
        print(f"\n✅ COMMIT MESSAGE:")
        print("  " + "-"*66)
        for line in (state.commit_message or "").split('\n'):
            print(f"  {line}")
        print("  " + "-"*66)
        
        # Optionally commit
        print("\n" + "-"*70)
        print("STEP 4: Commit (Optional)")
        print("-"*70)
        
        response = input("\nDo you want to commit with this message? (y/n): ")
        if response.lower() in ['y', 'yes']:
            repo.index.commit(state.commit_message)
            print("✓ Committed successfully!")
            
            # Show git log
            print("\nGit log:")
            for commit in repo.iter_commits(max_count=2):
                print(f"  {commit.hexsha[:7]} - {commit.message.split(chr(10))[0]}")
        else:
            print("Skipped commit")
        
    finally:
        # Cleanup
        print("\n" + "-"*70)
        print("Cleanup")
        print("-"*70)
        
        response = input(f"\nDelete test repository at {test_repo_path}? (y/n): ")
        if response.lower() in ['y', 'yes']:
            shutil.rmtree(test_repo_path)
            print("✓ Test repository deleted")
        else:
            print(f"Test repository preserved at: {test_repo_path}")
    
    print("\n" + "="*70)
    print("  Example Complete!")
    print("="*70 + "\n")


def demonstrate_individual_agents():
    """Demonstrate using agents individually."""
    print("\n" + "="*70)
    print("  Individual Agent Usage Example")
    print("="*70 + "\n")
    
    from llm_client import LLMClient, LLMConfig
    from agents import DiffAgent, SummaryAgent, CommitWriterAgent
    
    # Create mock state with sample data
    state = PipelineState()
    
    # Simulate DiffAgent output
    state.bullet_points = [
        "• Added new function `greet(name)` in hello.py",
        "• Added new function `calculate_sum(a, b)` in hello.py",
        "• Added new file `utils.py` with email validation",
        "• Added new file `config.json` with app configuration"
    ]
    
    print("📊 Simulated DiffAgent Output:")
    for bullet in state.bullet_points:
        print(f"  {bullet}")
    
    # Create LLM client
    print("\n🤖 Initializing LLM client...")
    try:
        llm_config = LLMConfig.from_env()
        llm_client = LLMClient(llm_config)
        print("✓ LLM client ready")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        print("This example requires a working LLM setup.")
        return
    
    # Run SummaryAgent
    print("\n📝 Running SummaryAgent...")
    summary_agent = SummaryAgent(llm_client)
    state = summary_agent.process(state)
    
    if state.summary:
        print(f"✓ Summary: {state.summary}")
    
    # Run CommitWriterAgent
    print("\n✉️  Running CommitWriterAgent...")
    commit_agent = CommitWriterAgent(llm_client, commit_style="conventional")
    state = commit_agent.process(state)
    
    if state.commit_message:
        print(f"✓ Commit Message:")
        for line in state.commit_message.split('\n'):
            print(f"  {line}")
    
    print("\n" + "="*70)
    print("  Individual Agent Example Complete!")
    print("="*70 + "\n")


def main():
    """Main function."""
    print("\n🤖 Git Commit Writer Pipeline - Examples\n")
    print("Choose an example:")
    print("  1. Complete pipeline with test repository")
    print("  2. Individual agent usage")
    print("  3. Exit")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        demonstrate_pipeline()
    elif choice == "2":
        demonstrate_individual_agents()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
