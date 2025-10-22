# Advanced Directory Mapper for LLMs

## Overview
`map_directory.py` is an advanced Python script that generates a comprehensive, tree-like representation of a directory structure. It includes file sizes, intelligent summaries of file contents (e.g., imports and definitions for code files, headers for Markdown files), total size calculations, and project type detection. The output is optimized for use as context in large language models (LLMs), enabling tasks like querying file locations, analyzing code structures, or navigating project contents. The script supports text or JSON output formats, caching for faster re-runs, depth limits, ignore patterns (including .gitignore integration), and token estimation for LLM compatibility.

This tool is particularly useful for developers and AI enthusiasts who want to feed structured file system information into LLMs without manual effort, streamlining workflows for code review, documentation search, or project onboarding.

## Features
- **Directory Tree Structure**: Visual representation using ASCII art for directories and files.
- **File Size Formatting**: Human-readable units (B, KB, MB, GB, TB, PB).
- **Intelligent File Summaries**: 
  - For Python files: Extracts imports, local imports, function/class definitions.
  - For Markdown/Text files: Extracts headers or previews initial lines.
  - For other files: Basic previews or error messages if unreadable.
- **Total Size and Statistics**: Computes total files, directories, size, estimated tokens, and skipped items.
- **Project Type Detection**: Automatically identifies common project types (e.g., Python, Node.js, Java Maven).
- **Ignore Patterns**: Supports custom ignores, base ignores (e.g., .git, venv), and .gitignore files.
- **Depth Limiting**: Restrict scanning to a maximum directory depth.
- **Caching**: Speeds up repeated runs by caching unchanged files; optional cache clearing.
- **Output Customization**: Text (with ASCII tree) or JSON formats; optional token budget pruning.
- **Progress Bar**: Real-time progress during scanning.
- **Error Handling**: Gracefully handles permissions, invalid paths, and parsing errors.

## Requirements
- Python 3.6+ (tested up to 3.12+).
- Standard libraries: `os`, `sys`, `json`, `time`, `argparse`, `fnmatch`, `ast`, `re`, `pathlib`, `datetime`.
- No external dependencies; all features use built-in modules.

To verify your Python installation, run:
```bash
python --version
```
Ensure it reports 3.6 or higher.

## Installation
1. Clone the repository from GitHub.
   ```bash
   git clone https://github.com/hacktivist211/DirectoryMapper.git
   cd DirectoryMapper
   ```
2. Ensure Python 3.6+ is installed (check with the command above).
3. No further setup is needed—run the script directly as described below.

## Usage
Run the script from the command line. It accepts a target directory (defaults to the current directory) and various optional arguments for customization. Always execute from the cloned repository directory or with the script in your PATH.

1. **Basic Run**: Map the current directory and save to the default output file (`directory_map.txt`).
   ```bash
   python map_directory.py
   ```

2. **Specify a Directory**: Map a specific directory.
   ```bash
   python map_directory.py /path/to/your/project
   ```

3. **Customize Output File**: Change the output file name.
   ```bash
   python map_directory.py --output custom_map.txt
   ```

4. **Output in JSON Format**: Generate JSON instead of text for easier parsing.
   ```bash
   python map_directory.py --format json
   ```

5. **Ignore Specific Patterns**: Add custom ignore patterns (space-separated) to skip files or directories matching wildcards.
   ```bash
   python map_directory.py -i "*.tmp" "backup/"
   ```

6. **Limit Depth**: Scan only up to a certain directory depth to avoid deep recursion.
   ```bash
   python map_directory.py -d 3
   ```

7. **Disable .gitignore Usage**: Prevent the script from reading and applying .gitignore files.
   ```bash
   python map_directory.py --no-gitignore
   ```

8. **Omit File Content Summaries**: Skip reading and summarizing file contents for faster execution or privacy.
   ```bash
   python map_directory.py --no-content
   ```

9. **Set Maximum Tokens**: Prune output if it exceeds a token budget (rough estimate: characters / 4) to fit LLM context windows.
   ```bash
   python map_directory.py --max-tokens 10000
   ```

10. **Enable Caching**: Use caching for faster re-runs on unchanged directories (cache stored as `.dir_mapper_cache.json` in the root).
    ```bash
    python map_directory.py --use-cache
    ```

11. **Clear Cache**: Clear the existing cache file before running a fresh scan.
    ```bash
    python map_directory.py --clear-cache
    ```

12. **Combined Example**: Map a directory with depth limit, custom ignores, JSON output, caching, and token limit.
    ```bash
    python map_directory.py /path/to/project -d 4 -i "*.log" "temp/" --format json --use-cache --output project_map.json --max-tokens 5000
    ```

### Command-Line Arguments
For a full list of options, run:
```bash
python map_directory.py --help
```

Below is a table summarizing all arguments:

| Argument              | Description                                                                 | Type/Options          | Default Value       | Required? | Example Command |
|-----------------------|-----------------------------------------------------------------------------|-----------------------|---------------------|-----------|-----------------|
| `directory`          | The target directory to map.                                                | String               | `.` (current dir)   | No       | `python map_directory.py /home/user/project` |
| `-o, --output`       | Output file name.                                                           | String               | `directory_map.txt` | No       | `python map_directory.py --output map.txt` |
| `--format`           | Output format.                                                              | `text` or `json`     | `text`              | No       | `python map_directory.py --format json` |
| `-i, --ignore`       | Space-separated patterns to ignore (e.g., files/directories).               | List of strings      | None                | No       | `python map_directory.py -i "*.pyc" "build/"` |
| `-d, --depth`        | Maximum depth to scan.                                                      | Integer              | None (unlimited)    | No       | `python map_directory.py -d 5` |
| `--no-gitignore`     | Disable using .gitignore files for ignores.                                 | Flag                 | Enabled             | No       | `python map_directory.py --no-gitignore` |
| `--no-content`       | Omit file content summaries.                                                | Flag                 | Disabled            | No       | `python map_directory.py --no-content` |
| `--max-tokens`       | Prune output to stay under this token budget (estimated).                   | Integer              | None                | No       | `python map_directory.py --max-tokens 5000` |
| `--use-cache`        | Enable caching for faster re-runs. Cache stored in `.dir_mapper_cache.json`.| Flag                 | Disabled            | No       | `python map_directory.py --use-cache` |
| `--clear-cache`      | Clear the cache before running.                                             | Flag                 | Disabled            | No       | `python map_directory.py --clear-cache` |

After running, the script:
- Displays a progress bar during scanning.
- Outputs statistics (files, dirs, size, skipped items) in the console.
- Saves the map to the specified file.
- Use the generated file (e.g., `directory_map.txt` or JSON) as context for LLMs to perform tasks like file navigation, code analysis, or content querying.

## Example Output
### Text Format
For a directory `/project` (Python project):
```
================================================================================
 Directory Map for: /project
 Project Type: Python
 Generated on: 2025-10-22 14:30:45
================================================================================
 Summary: 3 files, 2 directories | Total Size: 5.12 MB | Skipped: 5
--------------------------------------------------------------------------------

project/
├── data.csv (3.50 MB)
├── scripts/
│   └── process.py (10.20 KB)
│       > def main(...):
│       > class Processor:
│       Imports: os, pandas
└── readme.md (1.42 KB)
    - Overview
    - Features
    - Usage
```

### JSON Format
```json
{
  "project_type": "Python",
  "stats": {
    "files": 3,
    "dirs": 2,
    "size": 5368709,
    "tokens": 2048,
    "skipped": 5
  },
  "tree": {
    "name": "project",
    "path": "/project",
    "type": "directory",
    "children": [
      // ... (nested structure with summaries)
    ]
  }
}
```

## Notes
- **Supported File Summaries**: Limited to code extensions (e.g., .py, .js), docs (.md, .txt), and configs (.json, etc.). Others show previews or errors.
- **Caching**: Stored in `.dir_mapper_cache.json` in the target directory root. Only caches unchanged files based on modification time.
- **Token Estimation**: Rough heuristic (characters / 4); use `--max-tokens` for LLM prompt limits.
- **gitignore Integration**: Scans upward from the target directory to find and apply .gitignore patterns.
- **UTF-8 Encoding**: Handles special characters in file names.
- **Permission Errors**: Skipped with console warnings; not included in output.
- **Project Type Detection**: Based on key files (e.g., `requirements.txt` for Python). Defaults to "Unknown" if undetected.
- Feed the output file to your LLM for enhanced interactions, e.g., "Based on this directory map, where is the main script?"

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
   ```bash
   git clone https://github.com/hacktivist211/DirectoryMapper.git
   git checkout -b feature/your-feature
   ```
2. Make your changes and commit.
   ```bash
   git commit -m "Add your feature"
   ```
3. Push and submit a pull request.
   ```bash
   git push origin feature/your-feature
   ```
   Then, create a pull request on GitHub with a clear description of your changes, including any tests or documentation updates.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.