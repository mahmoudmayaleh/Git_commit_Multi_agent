"""
CSV → JSON converter for commit datasets

Converts a CSV file (downloaded from Kaggle or exported) into the
expected JSON schema used by the evaluation framework:

[ { "commit_hash": ..., "message": ..., "diff": ..., "timestamp": ... }, ... ]

Usage:
    python -m evaluation.src.csv_to_json --input evaluation/data/raw_dataset/commits.csv

The converter will try to auto-detect common column names for commit hash,
message, diff/patch and timestamp. See `--map` option for overrides.
"""

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Common candidate column names
COMMIT_HASH_CANDIDATES = [
    'commit_hash', 'sha', 'commit', 'id', 'hash', 'commitid', 'commit_id'
]
MESSAGE_CANDIDATES = [
    'message', 'commit_message', 'msg', 'title', 'summary', 'subject'
]
DIFF_CANDIDATES = [
    'diff', 'patch', 'changes', 'patch_text', 'unified_diff', 'diff_text'
]
TIMESTAMP_CANDIDATES = [
    'timestamp', 'date', 'datetime', 'created_at'
]


def detect_column(fieldnames: List[str], candidates: List[str]) -> Optional[str]:
    """Return first matching candidate found in fieldnames (case-insensitive)."""
    lower_map = {f.lower(): f for f in fieldnames}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def convert_csv_to_json(input_path: Path, output_path: Path, 
                        mapping: Dict[str, str] = None, delimiter: str = ',',
                        encoding: str = 'utf-8') -> Path:
    """Convert CSV to expected JSON schema and save to output_path."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    rows_out = []
    with open(input_path, 'r', encoding=encoding, errors='replace', newline='') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        fieldnames = reader.fieldnames or []

        # Determine mapping
        mapping = mapping or {}
        commit_col = mapping.get('commit_hash') or detect_column(fieldnames, COMMIT_HASH_CANDIDATES)
        message_col = mapping.get('message') or detect_column(fieldnames, MESSAGE_CANDIDATES)
        diff_col = mapping.get('diff') or detect_column(fieldnames, DIFF_CANDIDATES)
        ts_col = mapping.get('timestamp') or detect_column(fieldnames, TIMESTAMP_CANDIDATES)

        logger.info(f"Detected columns -> commit: {commit_col}, message: {message_col}, diff: {diff_col}, timestamp: {ts_col}")

        for i, row in enumerate(reader):
            commit_hash = (row.get(commit_col) if commit_col else None) or ''
            message = (row.get(message_col) if message_col else None) or ''
            diff = (row.get(diff_col) if diff_col else None) or ''
            timestamp = (row.get(ts_col) if ts_col else None) or ''

            # Clean fields
            commit_hash = commit_hash.strip()
            message = message.strip()
            diff = diff.strip()
            timestamp = timestamp.strip()

            # If diff column appears to be a path to a file, try to read file (not common)
            if diff and diff.endswith('.patch') and Path(diff).exists():
                try:
                    diff = Path(diff).read_text(encoding=encoding)
                except Exception:
                    pass

            item = {
                'commit_hash': commit_hash or f'row_{i}',
                'message': message,
                'diff': diff,
            }
            if timestamp:
                item['timestamp'] = timestamp

            rows_out.append(item)

    # Validate that required fields exist in output (at least message or diff non-empty)
    valid_count = sum(1 for r in rows_out if r.get('message') or r.get('diff'))
    if valid_count == 0:
        logger.warning('No valid message/diff data found in CSV after conversion')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rows_out, f, indent=2, ensure_ascii=False)

    logger.info(f'Wrote {len(rows_out)} entries to {output_path} (valid: {valid_count})')
    return output_path


def _parse_map_arg(map_args: List[str]) -> Dict[str, str]:
    mapping = {}
    for m in map_args or []:
        if '=' in m:
            k, v = m.split('=', 1)
            mapping[k.strip()] = v.strip()
    return mapping


def main(argv=None):
    parser = argparse.ArgumentParser(description='Convert commits CSV to expected JSON schema')
    parser.add_argument('--input', '-i', required=True, help='Path to input CSV file')
    parser.add_argument('--output', '-o', default='evaluation/data/raw_dataset/commits.json', help='Path to output JSON file')
    parser.add_argument('--delimiter', '-d', default=',', help='CSV delimiter (default: ,)')
    parser.add_argument('--encoding', default='utf-8', help='File encoding (default: utf-8)')
    parser.add_argument('--map', '-m', action='append', help='Override detected column mapping, e.g. --map commit_hash=sha --map message=title')
    parser.add_argument('--quiet', action='store_true', help='Suppress info logs')

    args = parser.parse_args(argv)
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    mapping = _parse_map_arg(args.map)

    try:
        out = convert_csv_to_json(Path(args.input), Path(args.output), mapping=mapping, delimiter=args.delimiter, encoding=args.encoding)
        print(f'Converted CSV -> JSON: {out}')
    except Exception as e:
        logger.error(f'Conversion failed: {e}')
        raise


if __name__ == '__main__':
    main()
