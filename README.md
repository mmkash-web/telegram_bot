To host your Telegram bot using a Virtual Private Server (VPS), follow these steps:

### Step 1: Choose a VPS Provider
Select a VPS provider. Popular options include:
- **DigitalOcean**
- **AWS (Amazon Web Services)**
- **Linode**
- **Vultr**
- **Hetzner**
- **OVH**

### Step 2: Create a VPS Instance
1. **Sign up** for the VPS provider of your choice.
2. **Create a new VPS instance** (usually referred to as a droplet, server, or instance).
   - Choose the **operating system** (Ubuntu, Debian, etc.).
   - Select a **plan** (CPU, RAM, storage).
   - Configure **additional settings** like backups or monitoring if needed.

### Step 3: Connect to Your VPS
Use an SSH client to connect to your VPS. For example, on Windows, you can use:
- **PuTTY**
- **Windows Terminal** (with SSH)
- **Termius** (if you want to use your phone)

On your terminal (Linux or macOS), use the command:
```bash
ssh root@your_server_ip
```
Replace `your_server_ip` with the IP address of your VPS.

### Step 4: Install Required Software
1. **Update the package list**:
   ```bash
   sudo apt update && sudo apt upgrade
   ```

2. **Install Python and pip** (if not installed):
   ```bash
   sudo apt install python3 python3-pip
   ```

3. **Install Git** (if you plan to clone your repository):
   ```bash
   sudo apt install git
   ```

4. **Install any other dependencies** required for your bot, such as `requests` and `python-telegram-bot`:
   ```bash
   pip install requests python-telegram-bot python-dotenv
   ```

### Step 5: Transfer Your Bot Code
You can transfer your code to the VPS in several ways:
- **Clone from GitHub**:
   ```bash
   git clone https://github.com/Emmkash20/autoscriptssh.git
   ```

- **Upload using SCP**:
   ```bash
   scp /path/to/your/local/bingwa_sokoni_bot.py root@your_server_ip:/path/to/destination
   ```

### Step 6: Configure Environment Variables
1. **Create a `.env` file** in the same directory as your bot script and add your API credentials:
   ```
   API_USERNAME=your_api_username
   API_PASSWORD=your_api_password
   BOT_TOKEN=your_bot_token
   ```

### Step 7: Run Your Bot
1. **Navigate to the directory** where your bot script is located:
   ```bash
   cd /path/to/your/bot
   ```

2. **Run the bot**:
   ```bash
   python3 bingwa_sokoni_bot.py
   ```

### Step 8: Keep Your Bot Running
To keep your bot running in the background, you can use:
- **Screen** or **tmux**:
   - Install `screen`:
     ```bash
     sudo apt install screen
     ```
   - Start a new session:
     ```bash
     screen
     ```
   - Run your bot, and then detach the session using `Ctrl + A`, followed by `D`.
   - To reattach, use:
     ```bash
     screen -r
     ```

- **Systemd Service**: Create a service file to manage your bot as a service.

### Step 9: Monitor Your Bot
Check logs and ensure that your bot is running smoothly. You can check logs or any output to diagnose issues.

### Step 10: Secure Your VPS
1. **Set up a firewall** (like UFW):
   ```bash
   sudo ufw allow OpenSSH
   sudo ufw enable
   ```

2. **Consider changing the SSH port** and disabling root login for added security.

### Conclusion
Once everything is set up, your Telegram bot will be hosted on your VPS and should be ready to respond to users. Make sure to test it thoroughly! If you have specific questions about any of the steps, feel free to ask!
