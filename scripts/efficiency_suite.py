import os
import argparse
from pathlib import Path
from google import genai

def count_tokens(text: str, model: str = "gemini-1.5-flash") -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return max(1, len(text) // 4)
    client = genai.Client(api_key=api_key)
    try:
        return client.models.count_tokens(model=model, contents=text).total_tokens
    except: return max(1, len(text) // 4)

def test_static(target_dir: Path):
    print(f"--- Static Analysis: {target_dir} ---")
    md_files = list(target_dir.rglob("*.md"))
    results = []
    for f in md_files:
        content = f.read_text()
        results.append({"file": str(f), "tokens": count_tokens(content)})
    
    # Simple overlap check: find common lines > 20 chars
    line_map = {}
    for f in md_files:
        lines = [l.strip() for l in f.read_text().splitlines() if len(l.strip()) > 20]
        for l in lines:
            if l not in line_map: line_map[l] = []
            line_map[l].append(str(f))
            
    overlaps = {l: files for l, files in line_map.items() if len(files) > 1}
    print(f"Found {len(overlaps)} redundant string patterns across {len(md_files)} files.")
    return overlaps

def test_goldfish(doc_path: Path):
    print(f"--- Goldfish Simulation: {doc_path} ---")
    doc_content = doc_path.read_text()
    # Simulate loading referenced files
    referenced_tokens = 0
    # ... logic to parse [file](path) ...
    total_payload = count_tokens(doc_content) + referenced_tokens
    print(f"Goldfish Payload: {total_payload} tokens")
    return total_payload

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-static", type=str)
    parser.add_argument("--test-goldfish", type=str)
    args = parser.parse_args()
    if args.test_static:
        test_static(Path(args.test_static))
    if args.test_goldfish:
        test_goldfish(Path(args.test_goldfish))
