"""Remove emojis from all markdown and Python files."""
import re
import os

def remove_emojis(text):
    """Remove emoji characters from text."""
    # Remove common emojis and symbols
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U00002600-\U000026FF"  # misc symbols
        "\u2714\u2716\u2728\u2764\u2705\u274C\u2B50\u26A0"  # check marks, stars, etc
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

def clean_file(filepath):
    """Clean emojis from a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned = remove_emojis(content)
        
        if cleaned != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            print(f"Cleaned: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error cleaning {filepath}: {e}")
        return False

# Clean all markdown files
md_files = [
    'README.md',
    'GETTING_STARTED.md',
    'CHANGELOG.md',
    'TROUBLESHOOTING.md',
    'USAGE.md',
    'API_REFERENCE.md',
    'PROJECT_STRUCTURE.md',
    'INDEX.md'
]

# Clean Python files
py_files = [
    'main.py',
    'pipeline.py',
    'agents/diff_agent.py',
    'agents/summary_agent.py',
    'agents/commit_writer_agent.py'
]

print("Removing emojis from files...")
cleaned_count = 0

for file in md_files + py_files:
    if os.path.exists(file):
        if clean_file(file):
            cleaned_count += 1

print(f"\nDone! Cleaned {cleaned_count} files.")
