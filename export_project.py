import os

# Cấu hình các loại file cần lấy nội dung và các thư mục cần bỏ qua
INCLUDE_EXTENSIONS = ('.sql', '.py')
EXCLUDE_DIRS = ('.git', 'venv', '__pycache__', '.pytest_cache')

def export_project(output_file='PROJECT_EXPORT.txt'):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk('.'):
            # Loại bỏ các thư mục không mong muốn
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file.endswith(INCLUDE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    
                    # Ghi đường dẫn file
                    outfile.write(f"\n{'='*20}\n")
                    outfile.write(f"FILE: {file_path}\n")
                    outfile.write(f"{'='*20}\n\n")
                    
                    # Ghi nội dung file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                        outfile.write("\n")
                    except Exception as e:
                        outfile.write(f"Could not read file: {e}\n")

    print(f"Đã export toàn bộ code vào file: {output_file}")

if __name__ == "__main__":
    export_project()