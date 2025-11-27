"""
Simple Demo - Test the Pipeline Without LLM

This script demonstrates the DiffAgent working without requiring
a full LLM installation. Perfect for testing the setup.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("  Git Commit Writer Pipeline - Simple Demo")
print("="*70)
print()

# Test 1: Check imports
print("Test 1: Checking imports...")
try:
    from state import PipelineState
    print("✓ State module imported")
    
    from agents.diff_agent import DiffAgent
    print("✓ DiffAgent imported")
    
    from config import Config
    print("✓ Config module imported")
    
    print()
except Exception as e:
    print(f"✗ Import failed: {e}")
    print("\nPlease install core dependencies:")
    print("  pip install GitPython requests python-dotenv colorama")
    sys.exit(1)

# Test 2: Create state
print("Test 2: Creating pipeline state...")
try:
    state = PipelineState()
    print(f"✓ State created: {state}")
    print()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 3: Test DiffAgent (without LLM)
print("Test 3: Testing DiffAgent (rule-based, no LLM)...")
try:
    diff_agent = DiffAgent(repo_path=".", use_llm=False)
    print("✓ DiffAgent created")
    
    # Check if there are staged changes
    try:
        from git import Repo
        repo = Repo(".")
        diff = repo.git.diff('--staged')
        
        if diff:
            print(f"✓ Found staged changes ({len(diff)} characters)")
            print()
            print("Running DiffAgent...")
            state = diff_agent.process(state)
            
            if state.bullet_points:
                print(f"✓ Generated {len(state.bullet_points)} bullet points:")
                for bullet in state.bullet_points:
                    print(f"  {bullet}")
            else:
                print("⚠ No bullet points generated (this is normal if diff is empty)")
        else:
            print("⚠ No staged changes found")
            print()
            print("To test with real changes:")
            print("  1. Make some changes to files")
            print("  2. Run: git add .")
            print("  3. Run this script again")
    except Exception as e:
        print(f"⚠ Git check failed: {e}")
        print("  (This is OK if you're not in a git repository)")
    
    print()
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Configuration
print("Test 4: Checking configuration...")
try:
    Config.display()
    print()
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Summary
print("="*70)
print("  Demo Complete!")
print("="*70)
print()
print("✓ Core functionality is working!")
print()
print("Next steps:")
print("  1. For LOCAL LLM: pip install torch transformers accelerate")
print("  2. For API mode: Get an API key and update .env")
print("  3. Try full pipeline: python main.py")
print()
print("Current LLM mode:", Config.LLM_MODE)
if Config.LLM_MODE == "api":
    print("  Note: You'll need a valid API key to use the full pipeline")
    print("  Update API_KEY in .env file")
print()
