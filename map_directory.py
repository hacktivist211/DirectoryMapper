import os
from pathlib import Path

def get_size_format(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def map_directory_structure(root_path, prefix="", is_last=True, output_lines=None):
    if output_lines is None:
        output_lines = []
    try:
        path = Path(root_path)
        connector = "└── " if is_last else "├── "
        if path.is_file():
            size = path.stat().st_size
            size_str = get_size_format(size)
            line = f"{prefix}{connector}{path.name} ({size_str})"
            output_lines.append(line)
        elif path.is_dir():
            line = f"{prefix}{connector}{path.name}/"
            output_lines.append(line)
            try:
                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                extension = "    " if is_last else "│   "
                new_prefix = prefix + extension
                for idx, item in enumerate(items):
                    is_last_item = (idx == len(items) - 1)
                    map_directory_structure(item, new_prefix, is_last_item, output_lines)
            except PermissionError:
                error_line = f"{prefix}{'    ' if is_last else '│   '}[Permission Denied]"
                output_lines.append(error_line)
    except Exception as e:
        error_line = f"{prefix}[Error: {str(e)}]"
        output_lines.append(error_line)
    return output_lines

def calculate_directory_size(path):
    total = 0
    try:
        for entry in Path(path).rglob('*'):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except:
                    pass
    except:
        pass
    return total

def main():
    directory_path = input("Enter the directory path to map: ")
    
    print("=" * 80)
    print(f"Directory Structure Map: {directory_path}")
    print("=" * 80)
    print()
    
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist or the path is invalid!")
        return
        
    print("Calculating total size...")
    total_size = calculate_directory_size(directory_path)
    print(f"Total Size: {get_size_format(total_size)}")
    print()
    
    root_path = Path(directory_path)
    root_line = f"{root_path.name}/ (Root)"
    print(root_line)
    output_lines = [root_line]
    
    try:
        items = sorted(root_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        for idx, item in enumerate(items):
            is_last = (idx == len(items) - 1)
            map_directory_structure(item, "", is_last, output_lines) 
    except PermissionError:
        error_line = "[Permission Denied for Root Directory]"
        print(error_line)
        output_lines.append(error_line)
    except Exception as e:
        error_line = f"[Error processing root directory: {str(e)}]"
        print(error_line)
        output_lines.append(error_line)
        
    print()
    print("=" * 80)
    
    for line in output_lines[1:]:
        print(line)
    print()
    print("=" * 80)

    output_file = "directory_structure.txt"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"Directory Structure Map: {directory_path}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Size: {get_size_format(total_size)}\n\n")
            f.write("\n".join(output_lines))
            f.write("\n\n" + "=" * 80)
        print(f"Output saved to: {output_file}")
    except Exception as e:
        print(f"Could not save to file: {str(e)}")

if __name__ == "__main__":
    main()
