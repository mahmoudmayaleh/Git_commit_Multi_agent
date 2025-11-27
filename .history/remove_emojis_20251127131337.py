"""Script to remove emojis from all files to make documentation professional."""

import re
from pathlib import Path

# Define emoji patterns to remove
EMOJI_PATTERNS = [
    r'🤖', r'📋', r'📝', r'✅', r'🔧', r'🔍', r'⏳', r'✓', r'✗', r'🚀',
    r'📊', r'⚙️', r'💡', r'🎯', r'⚡', r'🔥', r'👍', r'❌', r'⚠️', r'📁',
    r'📄', r'💻', r'🛠️', r'📌', r'🎨', r'🐛', r'♻️', r'🔀', r'⬆️', r'⬇️',
    r'➕', r'➖', r'🗑️', r'📦', r'🏷️', r'🏗️', r'🌟', r'⚠',
]

# Files to process
FILES_TO_CLEAN = [
    'README.md',
    'GETTING_STARTED.md',
    'USAGE.md',
    'CHANGELOG.md',
    'PROJECT_COMPLETE.md',
    'INDEX.md',
    'SETUP_STATUS.md',
    'API_REFERENCE.md',
]


def remove_emojis_from_text(text: str) -> str:
    """Remove all emojis from text."""
    for emoji in EMOJI_PATTERNS:
        # Remove emoji and any trailing space
        text = re.sub(f'{emoji}\\s*', '', text)
    return text


def clean_file(filepath: Path):
    """Remove emojis from a single file."""
    if not filepath.exists():
        print(f"Skipping {filepath} (not found)")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned_content = remove_emojis_from_text(content)
        
        if content != cleaned_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f"Cleaned: {filepath.name}")
        else:
            print(f"No changes: {filepath.name}")
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")


def main():
    """Clean all documentation files."""
    print("Removing emojis from documentation files...")
    print("=" * 60)
    
    base_path = Path(__file__).parent
    
    for filename in FILES_TO_CLEAN:
        filepath = base_path / filename
        clean_file(filepath)
    
    print("=" * 60)
    print("Done! All files processed.")


if __name__ == "__main__":
    main()
