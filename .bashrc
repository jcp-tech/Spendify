## Activate venv-linux if the folder exists
if [ -d "venv-linux" ] && [ -f "venv-linux/bin/activate" ]; then
    source "venv-linux/bin/activate"
    echo "Activated Python: $(which python)"
fi

## Source all .env files in the current directory and subdirectories
for env_file in $(find . -type f -name '*.env'); do # find . -type f -name '*.env' | while IFS= read -r env_file; do
    echo "Found: $env_file"
    set -a
    source "$env_file"
    set +a
done