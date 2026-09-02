"""Creates Desktop and Start Menu shortcuts for Circle to Search."""
import os
import sys
import subprocess

def find_pythonw():
    # 1. Same dir as current python executable
    cur_dir = os.path.dirname(sys.executable)
    cand1 = os.path.join(cur_dir, "pythonw.exe")
    if os.path.isfile(cand1):
        return cand1

    # 2. Common Python paths in LocalAppData
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        py_dir = os.path.join(local_app_data, "Programs", "Python")
        if os.path.isdir(py_dir):
            for entry in sorted(os.listdir(py_dir), reverse=True):
                cand2 = os.path.join(py_dir, entry, "pythonw.exe")
                if os.path.isfile(cand2):
                    return cand2

    # 3. Default fallback
    return "pythonw.exe"

def create_windows_shortcut(target_path, arguments, shortcut_path, working_dir, icon_path, description):
    ps_command = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{shortcut_path}')
$s.TargetPath = '{target_path}'
$s.Arguments = '{arguments}'
$s.WorkingDirectory = '{working_dir}'
$s.IconLocation = '{icon_path},0'
$s.Description = '{description}'
$s.Save()
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], check=True)

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(project_dir, "main.py")
    icon_ico = os.path.join(project_dir, "app_icon.ico")
    pythonw_path = find_pythonw()

    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    desktop = os.path.join(user_profile, "Desktop")
    start_menu = os.path.join(os.environ.get("APPDATA", user_profile), r"Microsoft\Windows\Start Menu\Programs")

    shortcuts = [
        os.path.join(desktop, "Circle to Search.lnk"),
        os.path.join(start_menu, "Circle to Search.lnk"),
        os.path.join(project_dir, "Circle to Search.lnk"),
    ]

    for shortcut in shortcuts:
        try:
            create_windows_shortcut(
                target_path=pythonw_path,
                arguments=f'"{main_py}"',
                shortcut_path=shortcut,
                working_dir=project_dir,
                icon_path=icon_ico,
                description="Circle to Search - Google Lens for Windows (Ctrl+Alt+C)",
            )
            print(f"[OK] Shortcut created: {shortcut}")
        except Exception as e:
            print(f"[ERR] Failed to create {shortcut}: {e}")

if __name__ == "__main__":
    main()
