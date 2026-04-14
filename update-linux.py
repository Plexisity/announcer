from urllib.request import urlretrieve
import os
import requests
import time
import discord
import asyncio
import dotenv
import subprocess
import sys
import stat
from pathlib import Path

timeout = 1
last_update_time = 0
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
channel_id = 1371637817058267139

# Load the token from the environment variable
dotenv.load_dotenv()
home_env = os.path.expanduser('~/.announcer/.env')
if os.path.exists(home_env):
	dotenv.load_dotenv(dotenv_path=home_env)
token = os.getenv("Ethan")
if not token:
	print("Token is missing or invalid. Check your .env file.")
	sys.exit(1)

token = token.strip()
print(f"Token length: {len(token)}")


def wifi_check():
	"""Check for an active internet connection."""
	try:
		requests.head("https://discord.com", timeout=timeout)
		print("The internet connection is active")
	except requests.ConnectionError:
		print("The internet connection is down, waiting for connection")
		time.sleep(1)
		wifi_check()

def create_autostart_desktop(target_script: str, name: str = "announcer"):
	"""Create a .desktop autostart entry for GNOME/KDE.

	target_script should be the full path to the script to execute.
	Uses the same Python interpreter that's running this updater.
	"""
	autostart_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'autostart'
	autostart_dir.mkdir(parents=True, exist_ok=True)
	desktop_path = autostart_dir / f"{name}.desktop"
	exec_cmd = f'"{sys.executable}" "{target_script}"'
	content = (
		"[Desktop Entry]\n"
		f"Type=Application\n"
		f"Exec={exec_cmd}\n"
		f"Hidden=false\n"
		f"NoDisplay=false\n"
		f"X-GNOME-Autostart-enabled=true\n"
		f"Name={name}\n"
		f"Comment=Announcer autostart\n"
	)
	try:
		desktop_path.write_text(content)
		desktop_path.chmod(0o644)
		print(f"Autostart desktop file created at {desktop_path}")
	except Exception as e:
		print(f"Failed to create autostart desktop file: {e}")

async def send_message(channel, message):
	"""Send a message to the Discord channel."""
	await channel.send(message)


def reporthook(block_num, block_size, total_size):
	"""Report download progress."""
	global last_update_time
	downloaded = block_num * block_size
	if total_size and total_size > 0:
		progress = downloaded / total_size * 100
	else:
		progress = 0.0
	current_time = time.time()

	if current_time - last_update_time >= 3:
		print(f"Download progress: {progress:.2f}%")
		try:
			asyncio.run_coroutine_threadsafe(
				send_message(client.get_channel(channel_id), f"Download progress: {progress:.2f}%"),
				client.loop
			)
		except Exception:
			pass
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
	"""Kill a process by name on Linux (tries pkill -f, then pgrep+kill)."""
	try:
		# First try pkill
		ret = subprocess.call(['pkill', '-f', process_name])
		if ret == 0:
			print(f"Sent pkill for {process_name}")
			return
		# Fallback: pgrep and kill
		p = subprocess.Popen(['pgrep', '-f', process_name], stdout=subprocess.PIPE, text=True)
		out, _ = p.communicate()
		if not out.strip():
			print(f"Process {process_name} not found.")
			return
		for pid in out.split():
			try:
				os.kill(int(pid), 15)
				print(f"Killed pid {pid}")
			except Exception as e:
				print(f"Failed to kill pid {pid}: {e}")
	except FileNotFoundError:
		print("pkill/pgrep not found on system; cannot kill process by name")
	except Exception as e:
		print(f"Error while killing process {process_name}: {e}")


async def handle_file_operations(downloaded_filename="index-linux.py"):
	"""Handle file operations like replacing and starting the file."""
	try:
		cwd = os.getcwd()
		install_dir = os.path.expanduser('~/.local/share/announcer')
		os.makedirs(install_dir, exist_ok=True)

		src_index = os.path.join(cwd, downloaded_filename)
		dst_index = os.path.join(install_dir, downloaded_filename)

		if os.path.exists(src_index):
			os.replace(src_index, dst_index)
			print(f"{downloaded_filename} moved to {dst_index}")
		else:
			print(f"{downloaded_filename} not found in current directory: {src_index}")

		# Ensure the main script is executable
		try:
			if os.path.exists(dst_index):
				st = os.stat(dst_index)
				os.chmod(dst_index, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
		except Exception:
			pass

		# Create autostart .desktop to run the installed script
		create_autostart_desktop(dst_index, name='announcer')

		# Start the main script using the same python interpreter
		def try_start(path):
			if not os.path.exists(path):
				print(f"Cannot start, file missing: {path}")
				return False
			try:
				subprocess.Popen([sys.executable, path], cwd=os.path.dirname(path), close_fds=True)
				print(f"Started {os.path.basename(path)} via subprocess")
				return True
			except Exception as e:
				print(f"Failed to start {path} via subprocess: {e}")
				return False

		try_start(dst_index)

	except FileNotFoundError as e:
		print("File not found during replace or start operation:", e)
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

	print("Autostart configured (if possible).")
	print(f"Logged in as {client.user}")
	print(f"Found channel: {channel.name}")

	# Kill the existing process if running
	await kill_process("index-linux.py")

	# Download index-linux.py (from latest_linux.txt)
	txt_url = "https://raw.githubusercontent.com/Plexisity/announcer/main/latest_linux.txt"
	url_index = get_latest_url(txt_url)
	if not url_index:
		print("Could not get the latest index URL. Exiting.")
		await client.close()
		return
	filename_index = os.path.basename(url_index) or "index-linux.py"
	if os.path.exists(filename_index):
		print(f"File {filename_index} already exists. Deleting it...")
		os.remove(filename_index)
	print(f"Starting download of {filename_index}...")
	await channel.send(f"Starting download of {filename_index}...")
	await download_file(url_index, filename_index)

	print("Download complete.")
	await channel.send("Download complete.")

	# Handle file operations (no backup handling)
	await handle_file_operations(downloaded_filename=filename_index)

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

