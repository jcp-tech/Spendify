# 📝 Documentation: Running a Discord Bot with `tmux` on Google Cloud VM

---
<!-- 
## Installing Python 3.10 on Ubuntu (GCP VM)

Before installing tmux and running your bot, it’s recommended to install Python 3.10 (for modern compatibility and support):

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-distutils python3-pip
pip install --no-cache-dir -r requirements.txt
python3.10 --version
```

To create your virtual environment with Python 3.10:

```bash
python3.10 -m venv venv
source venv/bin/activate
``` 
---
-->

## 1. Installing tmux, pip & venv

Connect to your VM via SSH, then run:

```bash
sudo apt update
sudo apt install tmux
sudo apt install python3-pip
apt install python3.11-venv
sudo apt update && sudo apt install git -y
git clone https://github.com/jcp-tech/Spendify.git
python3 -m venv ~/bot-venv
source ~/bot-venv/bin/activate
pip install --upgrade pip
cd Spendify/discord_bot/
pip install -r requirements.txt
nano ~/Spendify/discord_bot/.env
# Add the Env Settings.
```

---

## 2. Starting a tmux Session

Start a new session named `discordbot` (or use your own name):

```bash
tmux new -s discordbot
```

---

## 3. Running Your Bot Inside tmux

Navigate to your bot directory, activate your virtual environment, and start your bot:

```bash
cd ~/Spendify/discord_bot/        # Your project directory
source ~/bot-venv/bin/activate
python3 bot.py
```

---

## 4. Detaching and Reattaching

* **Detach (leave bot running):**
  Press `Ctrl + B`, then release both keys and press `D`.

* **Reattach (see your bot’s output):**

  ```bash
  tmux attach -t discordbot
  ```

---

## 5. Managing tmux Sessions

* **List all sessions:**

  ```bash
  tmux ls
  ```

* **Kill a session (stop the bot):**

  ```bash
  tmux kill-session -t discordbot
  ```

---

## 6. Updating the Code

To update your bot code and restart it:

```bash
cd ~/Spendify
git pull
cd discord_bot
tmux attach -t discordbot
# Stop the bot with Ctrl + C
source ~/bot-venv/bin/activate
python3 bot.py
```

* Use `Ctrl + C` inside tmux to stop the running bot.
* After updating, start the bot again with `python3 bot.py`.
* Press `Ctrl + B`, then release both keys and press `D`. (to Exit TMUX)

---

## 7. SSH Access to Your GCP VM

To SSH into your GCP VM from your local laptop:

**General format:**

```bash
ssh -i <path to private key> <username>@<ip address>
```

**Example (Windows):**

```bash
ssh -i C:\Users\JonathanChackoPattas\.ssh\seneca_temp azuread\jonathanchackopattas@34.132.211.201
```

> **Note:**
>
> * The `<path to private key>` is the location of your private SSH key (e.g., `seneca_temp`).
> * The `<username>` is your VM or Google Cloud OS login username.
> * The `<ip address>` is the external IP address of your VM.

**Public Key Setup (Required Once):**
Before connecting, you must add your public key (`seneca_temp.pub`) to the GCP VM's SSH keys. You can copy your public key using:

```powershell
Get-Content $env:USERPROFILE\.ssh\seneca_temp.pub
```

Paste the content into the SSH keys section of your GCP VM's settings under **Compute Engine → VM Instances → \[Your VM] → Edit → SSH Keys**.

---

## 8. Best Practices

* Always run long-lived scripts (like bots) in a `tmux` session—never directly in SSH!
* You can have multiple tmux sessions for different projects.
* If your SSH disconnects, your bot keeps running. Reconnect and reattach to monitor logs or restart your bot.

---

## 8. Quick Reference

| Action              | Command / Shortcut                    |
| ------------------- | ------------------------------------- |
| Start new session   | `tmux new -s <session_name>`          |
| Detach from session | `Ctrl + B`, then `D`                  |
| Create Alternative Key Bind | tmux set-option -g prefix C-a                  |
| Detach from session (alt) | `Ctrl + A`, then `D`                  |
| Reattach to session | `tmux attach -t <session_name>`       |
| List all sessions   | `tmux ls`                             |
| Kill a session      | `tmux kill-session -t <session_name>` |

---

## Moving Your Project Files to the GCP VM

To transfer your project files from your local Windows machine to your GCP VM, use the `scp` command (Secure Copy Protocol):

**General format:**

```bash
scp -i <path to private key> <local file path> <username>@<ip address>:<remote directory>
```

**Example command:**

```bash
scp -i "C:\Users\JonathanChackoPattas\.ssh\seneca_temp" "C:\Users\JonathanChackoPattas\OneDrive - Maritime Support Solutions\Desktop\Spendify\discord_bot\<local_file_name>" azuread\jonathanchackopattas@34.132.211.201:~/spendify_bot
```
scp -i "C:\Users\JonathanChackoPattas\.ssh\seneca_temp" "C:\Users\JonathanChackoPattas\OneDrive - Maritime Support Solutions\Desktop\Spendify\<local_file_name>" azuread\jonathanchackopattas@discord-bot-spendify-deploy:~/spendify_bot

> Repeat the command for each file you want to transfer.

**Project files to transfer:**

* requirements.txt
* bot.py
* .env

**Example destination:**

```
<username>@discord-bot-spendify-deploy:~/spendify_bot
```

You can also use wildcards or the `-r` option for directories if needed.

---

## Example Workflow

```bash
# 1. SSH into your VM
ssh -i ~/.ssh/gcp_key user@VM_IP

# 2. Install tmux
sudo apt update && sudo apt install tmux

# 3. Start tmux session
tmux new -s discordbot

# 4. Activate your Python environment and run your bot
python3 bot.py

# 5. Detach with Ctrl+B, then D

# 6. Reattach later with:
tmux attach -t discordbot
```

---

**Pro Tip:**
You can split tmux windows with `Ctrl+B`, then `%` (vertical) or `"` (horizontal), and scroll with `Ctrl+B`, then `[`.
Check `man tmux` or [tmux cheat sheets online](https://tmuxcheatsheet.com/) for more tricks!

---

**Done! Your bot is now running robustly on your Google Cloud VM, and you can monitor/restart it at any time.**