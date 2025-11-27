"""
Git Commit AI - Automated Commit Message Generator

A three-agent pipeline that uses Ollama + OpenChat 7B to generate professional
conventional commit messages from your staged Git changes.

REQUIREMENTS:
- Python 3.8+
- Git CLI
- Ollama (https://ollama.com)
- OpenChat 7B model: ollama pull openchat:7b

QUICK START:
1. Install Ollama and pull openchat:7b
2. Install dependencies: pip install -r requirements.txt
3. Stage your changes: git add .
4. Run: python main.py --dry-run

USAGE:
    python main.py                          # Generate and commit
    python main.py --dry-run                # Preview only, don't commit
    python main.py --verbose                # Show detailed agent outputs
    python main.py --output commit.txt      # Save message to file
    
CONFIGURATION:
Edit .env to customize:
- API_MODEL=openchat:7b (or any Ollama model)
- COMMIT_STYLE=conventional (or angular, gitmoji)
- DEBUG_MODE=true (to see intermediate outputs)

For more information, see README.md or visit https://ollama.com
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Colorama for colored terminal output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Fallback: no colors
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = ""
    class Style:
        BRIGHT = RESET_ALL = ""

from src.config import Config
from src.pipeline import CommitPipeline
from src.state import PipelineState


def setup_logging(verbose: bool = False):
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging (shows agent progress)
    """
    # Simplified, clean logging for better UX
    if verbose:
        log_level = logging.INFO
        log_format = '  %(levelname)s: %(message)s'
    else:
        # Only show errors in non-verbose mode
        log_level = logging.ERROR
        log_format = '%(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silence noisy third-party libraries
    logging.getLogger('git').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('requests').setLevel(logging.ERROR)


def print_banner():
    """Print application banner."""
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}{'='*70}
   Git Commit AI - Powered by Ollama + OpenChat 7B
{'='*70}{Style.RESET_ALL}
"""
    print(banner)


def print_stage_output(title: str, content: str, color=Fore.GREEN):
    """
    Print formatted stage output.
    
    Args:
        title: Stage title
        content: Content to display
        color: Color for the title
    """
    print(f"\n{color}{Style.BRIGHT}{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}{Style.RESET_ALL}")
    print(content)
    print()


def print_bullet_points(bullets: list):
    """Print bullet points in a formatted way."""
    for bullet in bullets:
        print(f"  {Fore.YELLOW}{bullet}{Style.RESET_ALL}")


def display_commit_message(commit_msg: str):
    """
    Display the final commit message in a formatted box.
    
    Args:
        commit_msg: Commit message to display
    """
    print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*70}")
    print("  GENERATED COMMIT MESSAGE")
    print(f"{'='*70}{Style.RESET_ALL}")
    print()
    
    # Display in a box
    lines = commit_msg.split('\n')
    max_len = max(len(line) for line in lines) + 4
    
    print(f"{Fore.CYAN}┌{'─' * max_len}┐{Style.RESET_ALL}")
    for line in lines:
        padding = ' ' * (max_len - len(line) - 2)
        print(f"{Fore.CYAN}│{Style.RESET_ALL} {line}{padding} {Fore.CYAN}│{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└{'─' * max_len}┘{Style.RESET_ALL}")
    print()


def confirm_commit() -> bool:
    """
    Ask user to confirm commit.
    
    Returns:
        True if user confirms
    """
    while True:
        response = input(f"{Fore.YELLOW}Do you want to commit with this message? (y/n): {Style.RESET_ALL}").lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")


def perform_commit(repo_path: str, commit_msg: str) -> bool:
    """
    Perform the actual git commit.
    
    Args:
        repo_path: Repository path
        commit_msg: Commit message
        
    Returns:
        True if successful
    """
    try:
        from git import Repo
        
        repo = Repo(repo_path)
        repo.index.commit(commit_msg)
        
        print(f"{Fore.GREEN}✓ Successfully committed!{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}✗ Commit failed: {e}{Style.RESET_ALL}")
        return False


def save_to_file(commit_msg: str, filepath: str):
    """
    Save commit message to file.
    
    Args:
        commit_msg: Message to save
        filepath: Output file path
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(commit_msg)
        print(f"{Fore.GREEN}✓ Saved to {filepath}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to save: {e}{Style.RESET_ALL}")


def main():
    """Main application entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generate Git commit messages using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--repo-path',
        type=str,
        default=None,
        help='Path to Git repository (default: current directory)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate message without committing'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--auto-commit',
        action='store_true',
        help='Commit without confirmation'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Save commit message to file'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show all intermediate outputs'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Print banner
    print_banner()
    
    # Display configuration
    if args.verbose or args.debug:
        Config.display()
    
    # Initialize pipeline
    try:
        print(f"{Fore.CYAN}Initializing pipeline...{Style.RESET_ALL}")
        
        pipeline = CommitPipeline(
            repo_path=args.repo_path,
            debug=args.debug
        )
        
        print(f"{Fore.GREEN}✓ Pipeline initialized{Style.RESET_ALL}\n")
        
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to initialize pipeline: {e}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Validate repository
    print(f"{Fore.CYAN}Checking for staged changes...{Style.RESET_ALL}")
    
    if not pipeline.validate_repository():
        print(f"{Fore.RED}✗ No staged changes found!{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Please stage your changes first:{Style.RESET_ALL}")
        print("  git add <files>")
        print("  git add .")
        sys.exit(1)
    
    print(f"{Fore.GREEN}✓ Found staged changes{Style.RESET_ALL}\n")
    
    # Run pipeline
    print(f"{Fore.CYAN}{Style.BRIGHT}Running pipeline...{Style.RESET_ALL}\n")
    
    state = pipeline.run()
    
    # Check for errors
    if state.has_errors():
        print(f"\n{Fore.RED}{'='*70}")
        print("  ✗ PIPELINE FAILED")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.RED}Errors:{Style.RESET_ALL}")
        for error in state.errors:
            print(f"  • {error}")
        
        sys.exit(1)
    
    # Pipeline already displayed the summary and changes during processing
    # Just show final separator before commit message
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'─'*70}{Style.RESET_ALL}\n")
    
    # Display commit message
    if state.commit_message:
        display_commit_message(state.commit_message)
        
        # Save to file if requested
        if args.output:
            save_to_file(state.commit_message, args.output)
        
        # Handle commit
        if not args.dry_run:
            should_commit = args.auto_commit or confirm_commit()
            
            if should_commit:
                perform_commit(pipeline.repo_path, state.commit_message)
            else:
                print(f"{Fore.YELLOW}Commit cancelled.{Style.RESET_ALL}")
                print(f"\nYou can commit manually with:")
                print(f'  git commit -m "{state.commit_message.split(chr(10))[0]}"')
        else:
            print(f"{Fore.YELLOW}Dry run mode - no commit performed{Style.RESET_ALL}")
    
    else:
        print(f"{Fore.RED}✗ Failed to generate commit message{Style.RESET_ALL}")
        sys.exit(1)
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Done!{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
