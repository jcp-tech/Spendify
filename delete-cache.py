import shutil, os
for root, dirs, files in os.walk(".", topdown=False):
    for d in dirs:
        if d == "__pycache__":
            print(f"Removing cache directory: {os.path.join(root, d)}")
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
