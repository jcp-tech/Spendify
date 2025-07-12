import os

folders = [
    'flask_api',
    'discord_bot',
    'adk_client',
]

def merge_files_from_subfolders(root_dir, filenames, folders=folders):
    # If folders is empty, use all subfolders in root_dir
    if not folders:
        folders = [name for name in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, name))]
    merged_contents = {fname: set() for fname in filenames}
    for folder in folders:
        folder_path = os.path.join(root_dir, folder)
        for fname in filenames:
            file_path = os.path.join(folder_path, fname)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    clean_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
                    merged_contents[fname].update(clean_lines)
    for fname in filenames:
        root_file = os.path.join(root_dir, fname)
        if os.path.exists(root_file):
            with open(root_file, 'r', encoding='utf-8') as f:
                existing_lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                merged_contents[fname].update(existing_lines)
        with open(root_file, 'w', encoding='utf-8') as f:
            for line in sorted(merged_contents[fname]):
                f.write(line + '\n')

if __name__ == "__main__":
    root_folder = os.path.dirname(os.path.abspath(__file__))
    merge_files_from_subfolders(root_folder, ['requirements.txt', '.env'])
