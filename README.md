# Directory Structure Mapper

## Overview
`map_directory.py` is a Python script that generates a tree-like representation of a directory structure, including file sizes, and saves it to a text file. This output is designed to be used as context for large language models (LLMs) to simplify interactions with local files, such as querying file locations or analyzing directory contents.

## Features
- **Directory Tree**: Creates a visual map of directories and files.
- **File Size Formatting**: Displays sizes in human-readable units (B, KB, MB, GB, TB).
- **Total Size Calculation**: Computes the total size of all files in the directory.
- **Error Handling**: Manages permission issues and invalid paths gracefully.
- **Output File**: Saves the structure to `directory_structure.txt` for easy LLM integration.

## Requirements
- Python 3.6+
- Standard libraries: `os`, `pathlib`

No external dependencies required.

## Usage
1. Run the script:
   ```bash
   python map_directory.py
   ```
2. Enter the directory path to map when prompted.
3. The script will:
   - Display the directory structure in the console.
   - Show the total directory size.
   - Save the structure to `directory_structure.txt`.
4. Use the generated `directory_structure.txt` as context for your LLM to interact with local files.

### Example Output
For a directory `/project`:
```
================================================================================
Directory Structure Map: /project
================================================================================

Total Size: 5.12 MB

project/ (Root)
├── data.csv (3.50 MB)
├── scripts/
│   └── process.py (10.20 KB)
└── readme.md (1.42 KB)

================================================================================
Output saved to: directory_structure.txt
```

Feed `directory_structure.txt` to your LLM to assist with tasks like file navigation or content analysis.

## Installation
1. Clone or download this repository.
2. Ensure Python 3.6+ is installed.
3. Run the script as described in **Usage**.

## Notes
- The script uses ASCII characters (`├──`, `└──`, `│`) for a clear tree structure.
- The output file is UTF-8 encoded to support special characters in file names.
- Permission errors are logged as `[Permission Denied]` in the output.
- Use the generated text file as structured context for LLMs to enhance file-related tasks.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a branch for your changes.
3. Submit a pull request with a clear description.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
