from urllib.request import urlretrieve
import os
import requests
import time
import discord
import asyncio
import dotenv
import win32com.client

timeout = 1
last_update_time = 0
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
channel_id = 1371637817058267139  # Replace with your channel ID

# Load the token from the environment variable
dotenv.load_dotenv(dotenv_path='C:\\announcer\\.env')
token = os.getenv("Ethan")
if not token:
    print("Token is missing or invalid. Check your .env file.")
    exit(1)

token = token.strip()  # Remove any extra whitespace or newline characters
print(f"Token length: {len(token)}")
print(f"Raw token value: {repr(token)}")


def wifi_check():
    """Check for an active internet connection."""
    try:
        requests.head("https://discord.com", timeout=timeout)
        print("The internet connection is active")
    except requests.ConnectionError:
        print("The internet connection is down, waiting for connection")
        time.sleep(1)
        wifi_check()

def create_shortcut():
    """Create a shortcut in the autostart folder."""
    autostart_path = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    shortcut_path = os.path.join(autostart_path, "announcer.lnk")
    target_path = "C:/announcer/update.exe"

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target_path
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.Description = "Announcer Update Script"
        shortcut.save()
        print("Shortcut created successfully.")
    except Exception as e:
        print(f"Failed to create shortcut: {e}")

create_shortcut()  # Create shortcut in autostart

async def send_message(channel, message):
    """Send a message to the Discord channel."""
    await channel.send(message)


def reporthook(block_num, block_size, total_size):
    """Report download progress."""
    global last_update_time
    downloaded = block_num * block_size
    progress = downloaded / total_size * 100
    current_time = time.time()

    if current_time - last_update_time >= 3:
        print(f"Download progress: {progress:.2f}%")
        asyncio.run_coroutine_threadsafe(
            send_message(client.get_channel(channel_id), f"Download progress: {progress:.2f}%"),
            client.loop
        )
        last_update_time = current_time

def get_latest_url(txt_url):
    """Fetch the latest download URL from a text file on GitHub."""
    try:
        response = requests.get(txt_url, timeout=timeout)
        response.raise_for_status()
        latest_url = response.text.strip()
        print(f"Latest download URL: {latest_url}")
        return latest_url
    except Exception as e:
        print(f"Failed to fetch latest URL: {e}")
        return None

async def download_file(url, filename):
    """Download a file asynchronously."""
    print(f"Starting download from {url} to {filename}...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, urlretrieve, url, filename, reporthook)
    print(f"Download finished for {filename}.")


async def kill_process(process_name):
    """Kill a process by name."""
    try:
        result = os.system(f"taskkill /f /im {process_name}")
        if result != 0:
            print(f"Process {process_name} not found or could not be terminated.")
    except Exception as e:
        print(f"Error while killing process {process_name}: {e}")


async def handle_file_operations():
    """Handle file operations like replacing and starting the file."""
    try:
        os.replace("index.exe", "C:/announcer/index.exe")
        print("File replaced successfully.")
        os.replace("ffmpeg.exe", "C:/announcer/ffmpeg.exe")
        os.startfile("C:/announcer/index.exe")
        print("File started successfully.")
    except FileNotFoundError:
        print("File not found during replace or start operation.")
    except Exception as e:
        print(f"Error during file operations: {e}")


@client.event
async def on_ready():
    """Handle the bot's readiness."""
    channel = client.get_channel(channel_id)
    if channel is None:
        print(f"Channel with ID {channel_id} not found.")
        await client.close()
        return

    print("Shortcut created in autostart folder.")
    print(f"Logged in as {client.user}")
    print(f"Found channel: {channel.name}")

    # Kill the existing process if running
    await kill_process("index.exe")

    # Download index.exe
    txt_url = "https://raw.githubusercontent.com/Plexisity/announcer/main/latest.txt"  # Update this to your actual txt file URL
    url_index = get_latest_url(txt_url)
    if not url_index:
        print("Could not get the latest index.exe URL. Exiting.")
        await client.close()
        return
    filename_index = "index.exe"
    if os.path.exists(filename_index):
        print(f"File {filename_index} already exists. Deleting it...")
        os.remove(filename_index)
    print("Starting download of index.exe...")
    await channel.send("Starting download of index.exe...")
    await download_file(url_index, filename_index)

    # Download ffmpeg.exe
    url_ffmpeg = "https://github.com/Plexisity/announcer/raw/main/ffmpeg.exe"
    filename_ffmpeg = "ffmpeg.exe"
    if os.path.exists(filename_ffmpeg):
        print(f"File {filename_ffmpeg} already exists. Deleting it...")
        os.remove(filename_ffmpeg)
    print("Starting download of ffmpeg.exe...")
    await channel.send("Starting download of ffmpeg.exe...")
    await download_file(url_ffmpeg, filename_ffmpeg)

    print("Download complete.")
    await channel.send("Download complete.")

    # Handle file operations
    await handle_file_operations()

    # Close the bot
    await client.close()


async def main():
    """Main entry point for the bot."""
    try:
        await client.start(token)
    except KeyboardInterrupt:
        print("Shutting down...")
        await client.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        await client.close()


if __name__ == "__main__":
    wifi_check()  # Ensure internet connection before starting
    asyncio.run(main())