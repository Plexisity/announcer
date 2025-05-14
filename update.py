from urllib.request import urlretrieve
import os
import requests
import time
import discord
import asyncio
import dotenv



timeout = 1
last_update_time = 0
connection = False
intents = discord.Intents.default()
client = discord.Client(intents=intents)
channel_id = 1371637817058267139  # Replace with your channel ID
token = os.getenv("Ethan").strip # Replace with your token

# Try loading from the current working directory first
loaded = dotenv.load_dotenv()
print(f"dotenv loaded (from current dir): {loaded}")
if not loaded:
    # If not found, try loading from the C:\announcer directory explicitly
    loaded = dotenv.load_dotenv(dotenv_path='C:\\announcer\\.env')
    print(f"dotenv loaded (from C:\\announcer): {loaded}")

token = os.getenv("Ethan")  # Replace with your token
print(f"Token value: {token}")

def wifi_check():
    global connection
    try:
        requests.head("http://discord.com/", timeout=timeout)
        # Connection Success
        print('The internet connection is active')
        connection = True
    except requests.ConnectionError:
        # Connection Retry
        print("The internet connection is down, waiting for connection")
        connection = False
        time.sleep(1)
        wifi_check()

wifi_check()

async def send_message(channel, message):
    await channel.send(message)

def reporthook(block_num, block_size, total_size):
    global last_update_time
    downloaded = block_num * block_size
    progress = downloaded / total_size * 100
    current_time = time.time()
    
    if current_time - last_update_time >= 3:
        asyncio.run_coroutine_threadsafe(send_message(channel, f"Download progress: {progress:.2f}%"), client.loop)
        last_update_time = current_time



async def download_file(url, filename):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, urlretrieve, url, filename, reporthook)

@client.event
async def on_ready():
    global channel
    channel = client.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found.")
        await client.close()
        return

    print(f'Logged in as {client.user}')
    print(f'Found channel: {channel.name}')

    os.system("taskkill /f /im index.exe")
    url = "https://github.com/Plexisity/announcer/raw/main/index.exe"
    filename = "index.exe"

    # Make C:/announcer/update.exe start on startup
    startup_path = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    shortcut_path = os.path.join(startup_path, "update.lnk")
    if not os.path.exists(shortcut_path):
        os.system(f'shortcut /f:"{shortcut_path}" /a:c /t:"C:/announcer/update.exe"')
    # Create the shortcut
    os.system(f'shortcut /f:"{shortcut_path}" /a:c /t:"C:/announcer/update.exe"')
    # Check if the shortcut was created successfully
    if os.path.exists(shortcut_path):
        print("Shortcut created successfully.")
    else:
        print("Failed to create shortcut.")

    # Send a message to the channel

    print("Starting download...")
    await channel.send("Starting download...")
    await download_file(url, filename)
    print("Download complete.")
    await channel.send("Download complete.")

    os.replace("index.exe", "C:/announcer/index.exe")
    os.startfile("C:/announcer/index.exe")
    await client.close()

# Load the token from the environment variable
if not token:
    print("Token is missing or invalid. Check your .env file.")
    exit(1)

token = token.strip()  # Remove any extra whitespace or newline characters
print(f"Token length: {len(token)}")
print(f"Raw token value: {repr(token)}")
if len(token) != 72:  # Bot tokens are typically 59 characters long
    print("Token length is incorrect. Verify the token in your .env file.")
    exit(1)

try:
    client.run(token)  # Run the bot
except discord.errors.LoginFailure as e:
    print(f"Login failed: {e}")