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
from urllib.parse import urlparse, unquote

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

# Globals for installed state
INSTALL_DIR = os.path.expanduser('~/.local/share/announcer')
last_installed_url = None
last_installed_basename = None
last_start_with_python = True
update_lock = None


def wifi_check():
	"""Check for an active internet connection."""
	try:
		requests.head("https://discord.com", timeout=timeout)
		print("The internet connection is active")
	except requests.ConnectionError:
		print("The internet connection is down, waiting for connection")
		time.sleep(1)
		wifi_check()


def create_autostart_desktop(target_script: str, name: str = "announcer", start_with_python: bool = True):
	"""Create a .desktop autostart entry for GNOME/KDE.

	target_script should be the full path to the script to execute.
	If `start_with_python` is True the Exec will run the current Python
	interpreter with the script as an argument; otherwise Exec will be the
	path to the executable.
	"""
	autostart_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'autostart'
	autostart_dir.mkdir(parents=True, exist_ok=True)
	desktop_path = autostart_dir / f"{name}.desktop"
	if start_with_python:
		exec_cmd = f'"{sys.executable}" "{target_script}"'
	else:
		exec_cmd = f'"{target_script}"'
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
	"""Send a message to the Discord channel (async)."""
	if channel is None:
		return
	try:
		await channel.send(message)
	except Exception:
		# Ignore send errors
		pass


def reporthook(block_num, block_size, total_size):
	"""Report download progress; called from urlretrieve."""
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
	"""Download a file asynchronously using urlretrieve in a thread."""
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


async def handle_file_operations(downloaded_filename="index-linux.py", start_with_python: bool = True):
	"""Move the downloaded file into install dir, make executable and start it."""
	try:
		cwd = os.getcwd()
		os.makedirs(INSTALL_DIR, exist_ok=True)

		src_index = os.path.join(cwd, downloaded_filename)
		dst_index = os.path.join(INSTALL_DIR, downloaded_filename)

		if os.path.exists(src_index):
			os.replace(src_index, dst_index)
			print(f"{downloaded_filename} moved to {dst_index}")
		else:
			print(f"{downloaded_filename} not found in current directory: {src_index}")

		# Ensure the main script/binary is executable
		try:
			if os.path.exists(dst_index):
				st = os.stat(dst_index)
				os.chmod(dst_index, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
		except Exception:
			pass

		# Create autostart .desktop to run the installed script
		create_autostart_desktop(dst_index, name='announcer', start_with_python=start_with_python)

		# Start the main program. Use Python when requested, otherwise execute directly.
		try:
			if start_with_python:
				subprocess.Popen([sys.executable, dst_index], cwd=os.path.dirname(dst_index), close_fds=True)
			else:
				subprocess.Popen([dst_index], cwd=os.path.dirname(dst_index), close_fds=True)
			print(f"Started {os.path.basename(dst_index)} via subprocess")
		except Exception as e:
			print(f"Failed to start {dst_index} via subprocess: {e}")

	except FileNotFoundError as e:
		print("File not found during replace or start operation:", e)
	except Exception as e:
		print(f"Error during file operations: {e}")


async def perform_update_from_txt(txt_url, channel=None):
	"""Download latest URL from `txt_url`, install and start it.

	This function is safe to call repeatedly; it uses an async lock to avoid
	concurrent updates.
	"""
	global last_installed_url, last_installed_basename, last_start_with_python, update_lock
	if update_lock is None:
		update_lock = asyncio.Lock()

	async with update_lock:
		url_index = get_latest_url(txt_url)
		if not url_index:
			print("Could not get latest URL in perform_update_from_txt")
			return None

		parsed = urlparse(url_index)
		remote_basename = os.path.basename(parsed.path)
		if remote_basename:
			remote_basename = unquote(remote_basename)
		else:
			remote_basename = "index-linux"

		local_temp = "index_download.tmp"
		if os.path.exists(local_temp):
			os.remove(local_temp)
		print(f"Starting download from {url_index} to temporary file...")
		if channel:
			await send_message(channel, "Starting download of index (temporary)...")
		await download_file(url_index, local_temp)

		# Inspect the downloaded file
		is_executable = False
		try:
			with open(local_temp, 'rb') as f:
				header = f.read(4)
				f.seek(0)
				sample = f.read(4096)
			if header.startswith(b'\x7fELF'):
				is_executable = True
		except Exception as e:
			print(f"Failed to inspect downloaded file: {e}")

		# Choose a safe final filename
		if is_executable:
			final_name = remote_basename
		else:
			if remote_basename.endswith('.py'):
				final_name = remote_basename
			else:
				final_name = f"{remote_basename}.py"

		if os.path.exists(final_name):
			os.remove(final_name)
		os.replace(local_temp, final_name)

		start_with_python = not is_executable

		print(f"Download complete: {final_name}")
		if channel:
			await send_message(channel, f"Downloaded {final_name}")

		# Install and start
		await handle_file_operations(downloaded_filename=final_name, start_with_python=start_with_python)

		# Remember what we installed
		last_installed_url = url_index
		last_installed_basename = final_name
		last_start_with_python = start_with_python

		return final_name


async def monitor_loop(txt_url, channel=None, check_interval: int = 10):
	"""Monitor the installed program and update/restart when it stops."""
	global last_installed_url, last_installed_basename, last_start_with_python
	while True:
		pattern = last_installed_basename or 'index-linux'
		try:
			ret = subprocess.run(['pgrep', '-f', pattern], stdout=subprocess.PIPE)
			if ret.returncode == 0:
				await asyncio.sleep(check_interval)
				continue
		except Exception:
			pass

		print(f"Detected `{pattern}` not running; checking for updates / restarting...")
		if channel:
			try:
				await send_message(channel, f"Detected `{pattern}` not running; checking for updates...")
			except Exception:
				pass

		url_index = get_latest_url(txt_url)
		if url_index and url_index != last_installed_url:
			print("New update available; performing update...")
			try:
				await perform_update_from_txt(txt_url, channel=channel)
			except Exception as e:
				print(f"Update during monitor failed: {e}")
		else:
			if last_installed_basename:
				installed_path = os.path.join(INSTALL_DIR, last_installed_basename)
				if os.path.exists(installed_path):
					try:
						if last_start_with_python:
							subprocess.Popen([sys.executable, installed_path], cwd=os.path.dirname(installed_path), close_fds=True)
						else:
							subprocess.Popen([installed_path], cwd=os.path.dirname(installed_path), close_fds=True)
						print("Restarted installed program.")
						if channel:
							try:
								await send_message(channel, f"Restarted {last_installed_basename}")
							except Exception:
								pass
					except Exception as e:
						print(f"Failed to restart installed program: {e}")
				else:
					print("Installed file missing; performing update...")
					try:
						await perform_update_from_txt(txt_url, channel=channel)
					except Exception as e:
						print(f"Update failed: {e}")
			else:
				print("No installed basename known; performing initial update...")
				try:
					await perform_update_from_txt(txt_url, channel=channel)
				except Exception as e:
					print(f"Initial update failed: {e}")

		await asyncio.sleep(check_interval)


@client.event
async def on_ready():
	"""Handle the bot's readiness: perform initial update and start monitor."""
	channel = client.get_channel(channel_id)
	if channel is None:
		print(f"Channel with ID {channel_id} not found.")
		await client.close()
		return

	print("Autostart configured (if possible).")
	print(f"Logged in as {client.user}")
	print(f"Found channel: {channel.name}")

	# Kill any existing index process
	await kill_process('index-linux')

	# Start update lock and perform initial update, then start monitor
	txt_url = "https://raw.githubusercontent.com/Plexisity/announcer/main/latest_linux.txt"
	global update_lock
	update_lock = asyncio.Lock()

	try:
		await perform_update_from_txt(txt_url, channel=channel)
	except Exception as e:
		print(f"Initial perform_update failed: {e}")

	# Start background monitor task to restart/update when the program stops
	asyncio.create_task(monitor_loop(txt_url, channel=channel, check_interval=10))

	print("Updater is monitoring the installed program; bot remains connected.")


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
