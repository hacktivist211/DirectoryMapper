import os
import sys
import json
import time
import argparse
import fnmatch
import ast
import re
from pathlib import Path
from datetime import datetime

SUPPORTED_CODE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.php'}
SUPPORTED_DOCS_EXTENSIONS = {'.md', '.txt'}
SUPPORTED_CONFIG_EXTENSIONS = {'.json', '.yaml', '.yml', '.toml', '.xml'}

class ProgressBar:
    def __init__(self, total, description="", width=50):
        self.total = max(total, 1)
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()

    def update(self, amount=1):
        self.current += amount
        self._display()

    def _display(self):
        percent = min(100, (self.current / self.total) * 100)
        filled = int(self.width * self.current // self.total)
        bar = '█' * filled + '─' * (self.width - filled)
        sys.stdout.write(f'\r{self.description:<25} [{bar}] {percent:.1f}%')
        sys.stdout.flush()

    def complete(self):
        print()

def get_size_format(size_bytes):
    if size_bytes is None: return "N/A"
    if size_bytes == 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def estimate_tokens(text):
    return len(text) // 4

def parse_python_file(content):
    summary = {"imports": [], "local_imports": [], "definitions": []}
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    summary["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    summary["local_imports"].append(f".{node.module}" if node.module else ".")
                else:
                    summary["imports"].append(node.module)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                summary["definitions"].append(f"def {node.name}(...):")
            elif isinstance(node, ast.ClassDef):
                summary["definitions"].append(f"class {node.name}:")
    except SyntaxError:
        return {"error": "SyntaxError parsing file."}
    return summary

def parse_markdown_file(content):
    headers = re.findall(r'^(#+)\s+(.*)', content, re.MULTILINE)
    return {"headers": [f"{'  ' * (len(h[0]) - 1)}- {h[1]}" for h in headers]}

def get_intelligent_summary(file_path, content_lines):
    ext = file_path.suffix.lower()
    content = "\n".join(content_lines)
    
    if ext == '.py':
        return parse_python_file(content)
    if ext in SUPPORTED_DOCS_EXTENSIONS:
        return parse_markdown_file(content)
    
    return {"preview": content_lines[:5]}

def load_gitignore_patterns(root_path):
    patterns = []
    current_path = root_path
    git_root = None

    while current_path.parent != current_path:
        if (current_path / ".git").is_dir():
            git_root = current_path
            break
        current_path = current_path.parent
    
    if not git_root: return patterns

    search_path = git_root
    while search_path != root_path.parent and search_path in root_path.parents:
        gitignore_file = search_path / ".gitignore"
        if gitignore_file.is_file():
            try:
                with open(gitignore_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        stripped = line.strip()
                        if stripped and not stripped.startswith('#'):
                            patterns.append(stripped)
            except IOError:
                pass
        search_path = list(filter(lambda p: p.parent == search_path, root_path.parents))
        if not search_path: break
        search_path = search_path[0]

    return patterns

def should_ignore(path, ignore_patterns):
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(str(path), pattern):
            return True
    return False

def map_directory(root_path, args, cache):
    base_ignore = {".git", ".vscode", "__pycache__", "node_modules", "venv"}
    gitignore_patterns = load_gitignore_patterns(root_path) if args.use_gitignore else []
    ignore_patterns = set(args.ignore or []) | base_ignore | set(gitignore_patterns)

    tree = {"name": root_path.name, "path": str(root_path), "type": "directory", "children": []}
    stats = {"files": 0, "dirs": 0, "size": 0, "tokens": 0, "skipped": 0}
    
    paths_to_process = []
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        original_dirs = dirnames[:]
        dirnames[:] = [d for d in original_dirs if not should_ignore(Path(d), ignore_patterns)]
        stats["skipped"] += len(original_dirs) - len(dirnames)
        
        current_depth = Path(dirpath).relative_to(root_path).parts
        if args.depth is not None and len(current_depth) >= args.depth:
            stats["skipped"] += len(dirnames)
            dirnames[:] = []
        
        paths_to_process.extend([Path(dirpath, name) for name in dirnames])
        paths_to_process.extend([Path(dirpath, name) for name in filenames])

    progress = ProgressBar(len(paths_to_process), "Mapping directory")

    node_stack = [(tree, root_path, 0)]
    
    while node_stack:
        parent_node, current_path, depth = node_stack.pop()
        
        if args.depth is not None and depth >= args.depth:
            continue
            
        try:
            entries = sorted(os.scandir(current_path), key=lambda e: (e.is_file(), e.name.lower()))
        except (PermissionError, FileNotFoundError):
            continue

        for entry in entries:
            progress.update()
            entry_path = Path(entry.path)
            if should_ignore(entry_path, ignore_patterns):
                stats["skipped"] += 1
                continue

            mod_time = entry.stat().st_mtime
            if args.use_cache and str(entry_path) in cache and cache[str(entry_path)]["mtime"] == mod_time:
                file_node = cache[str(entry_path)]["node"]
            else:
                file_node = {
                    "name": entry.name,
                    "path": str(entry_path),
                    "mtime": mod_time
                }
                if entry.is_dir():
                    file_node.update({"type": "directory", "children": []})
                    stats["dirs"] += 1
                    node_stack.append((file_node, entry_path, depth + 1))
                else:
                    size = entry.stat().st_size
                    file_node.update({"type": "file", "size": size})
                    stats["files"] += 1
                    stats["size"] += size
                    
                    if args.no_content:
                        file_node["summary"] = "Content omitted by user."
                    else:
                        try:
                            with open(entry_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content_lines = f.readlines(8192)
                            summary = get_intelligent_summary(entry_path, content_lines)
                            file_node["summary"] = summary
                        except Exception:
                            file_node["summary"] = {"error": "Could not read or parse file."}
            
            if args.use_cache:
                cache[str(entry_path)] = {"mtime": mod_time, "node": file_node}

            parent_node["children"].append(file_node)
    
    progress.complete()
    return tree, stats

def generate_text_output(node, prefix="", is_last=True):
    lines = []
    connector = "└── " if is_last else "├── "
    line = f"{prefix}{connector}{node['name']}"
    
    if node['type'] == 'directory':
        lines.append(line + "/")
        extension = "    " if is_last else "│   "
        new_prefix = prefix + extension
        for i, child in enumerate(node.get('children', [])):
            lines.extend(generate_text_output(child, new_prefix, i == len(node['children']) - 1))
    else:
        size_str = get_size_format(node.get('size'))
        line += f" ({size_str})"
        lines.append(line)
        summary = node.get('summary', {})
        if summary:
            summary_prefix = prefix + ("    " if is_last else "│   ")
            if 'error' in summary:
                 lines.append(f"{summary_prefix}  [!] {summary['error']}")
            if 'headers' in summary:
                for header in summary['headers'][:3]: lines.append(f"{summary_prefix}  - {header}")
            if 'definitions' in summary:
                for definition in summary['definitions'][:3]: lines.append(f"{summary_prefix}  > {definition}")
            if 'local_imports' in summary and summary['local_imports']:
                lines.append(f"{summary_prefix}  Imports: {', '.join(summary['local_imports'])}")

    return lines

def detect_project_type(root_path):
    if any(root_path.glob('*.sln')) or any(root_path.glob('*.csproj')):
        return "C# .NET"
    if (root_path / 'pom.xml').exists():
        return "Java Maven"
    if (root_path / 'package.json').exists():
        return "Node.js"
    if (root_path / 'requirements.txt').exists() or (root_path / 'pyproject.toml').exists():
        return "Python"
    if (root_path / 'Cargo.toml').exists():
        return "Rust"
    if (root_path / 'go.mod').exists():
        return "Go"
    return "Unknown"

def main():
    print("\n" + "="*80)
    print(" " * 24 + "Advanced Directory Mapper for LLMs")
    print("="*80)

    parser = argparse.ArgumentParser(
        description="Generate a comprehensive directory map for LLM context.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("directory", nargs="?", default=".", help="The target directory (defaults to current).")
    parser.add_argument("-o", "--output", default="directory_map.txt", help="Output file name.")
    parser.add_argument("--format", choices=['text', 'json'], default='text', help="Output format.")
    parser.add_argument("-i", "--ignore", nargs="+", help="Space-separated list of patterns to ignore.")
    parser.add_argument("-d", "--depth", type=int, help="Maximum depth to scan.")
    parser.add_argument("--no-gitignore", action="store_false", dest="use_gitignore", help="Do not use .gitignore files.")
    parser.add_argument("--no-content", action="store_true", help="Omit all file content summaries.")
    parser.add_argument("--max-tokens", type=int, help="Prune output to stay under this token budget (heuristic).")
    parser.add_argument("--use-cache", action="store_true", help="Enable caching to speed up subsequent runs.")
    parser.add_argument("--clear-cache", action="store_true", help="Clear the cache before running.")
    
    args = parser.parse_args()

    root_path = Path(args.directory).resolve()
    cache_file = root_path / ".dir_mapper_cache.json"

    if not root_path.is_dir():
        print(f"\n[ERROR] Directory '{root_path}' does not exist.")
        return

    cache = {}
    if args.clear_cache and cache_file.exists():
        print("[INFO] Clearing cache.")
        os.remove(cache_file)
    if args.use_cache and cache_file.exists():
        print("[INFO] Loading cache from:", cache_file)
        with open(cache_file, 'r') as f:
            cache = json.load(f)

    start_time = time.time()
    tree, stats = map_directory(root_path, args, cache)
    project_type = detect_project_type(root_path)
    
    output_content = ""
    if args.format == 'json':
        json_data = {"project_type": project_type, "stats": stats, "tree": tree}
        output_content = json.dumps(json_data, indent=2)
    else:
        header = [
            f"{'='*80}",
            f" Directory Map for: {root_path}",
            f" Project Type: {project_type}",
            f" Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*80}",
            f" Summary: {stats['files']} files, {stats['dirs']} directories | Total Size: {get_size_format(stats['size'])} | Skipped: {stats['skipped']}",
            f"{'-'*80}\n"
        ]
        tree_lines = generate_text_output(tree)
        output_content = "\n".join(header + tree_lines)

    if args.max_tokens:
        estimated_tokens = estimate_tokens(output_content)
        if estimated_tokens > args.max_tokens:
            print(f"[WARN] Output ({estimated_tokens} tokens) exceeds budget ({args.max_tokens}). Pruning...")
            scale = args.max_tokens / estimated_tokens
            output_content = output_content[:int(len(output_content) * scale)]
            output_content += "\n\n[... OUPUT PRUNED TO FIT TOKEN BUDGET ...]"

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"\n[SUCCESS] Map saved to '{args.output}'")
    except IOError as e:
        print(f"\n[ERROR] Could not write to file: {e}")

    if args.use_cache:
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f)
            print(f"[INFO] Cache updated at '{cache_file}'")
        except IOError:
            print("[WARN] Could not save cache file.")

    end_time = time.time()
    print("\n" + "="*80)
    print(" " * 32 + "TASK COMPLETE")
    print("="*80)
    print(f"  - Project Type: {project_type}")
    print(f"  - Time Taken:   {end_time - start_time:.2f} seconds")
    print(f"  - Output Format:  {args.format.upper()}")
    print(f"  - Total Size:     {get_size_format(stats['size'])}")
    print(f"  - Final Output:   {args.output}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

