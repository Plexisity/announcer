import os
import shutil
import time

#wait 5 seconds

time.sleep(5)
#kill index.exe if it is running
os.system("taskkill /f /im index.exe")
#delete the shortcut in autostart
def delete_shortcut():
    """Delete the shortcut in the autostart folder."""
    autostart_path = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    shortcut_path = os.path.join(autostart_path, "announcer.lnk")

    try:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print("Shortcut deleted successfully.")
        else:
            print("Shortcut does not exist.")
    except Exception as e:
        print(f"Failed to delete shortcut: {e}")

#delete contents of C:/announcerr and then delete the folder
def delete_folder_contents(folder_path):
    """Delete all contents of the specified folder."""
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        print(f"All contents of {folder_path} deleted successfully.")
    except Exception as e:
        print(f"Error deleting contents of {folder_path}: {e}")
    finally:
        # Delete the folder itself
        try:
            os.rmdir(folder_path)
            print(f"Folder {folder_path} deleted successfully.")
        except Exception as e:
            print(f"Error deleting folder {folder_path}: {e}")

delete_folder_contents("C:/announcer")
delete_shortcut()