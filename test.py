import subprocess
import time
import win32gui
import win32process
import psutil
import os

def enum_windows_callback(hwnd, windows):
    """Callback function to enumerate all visible windows"""
    if win32gui.IsWindowVisible(hwnd):
        window_text = win32gui.GetWindowText(hwnd)
        if window_text:
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process_name = psutil.Process(pid).name()
                windows.append((hwnd, window_text, process_name, pid))
            except:
                windows.append((hwnd, window_text, "Unknown", 0))

def get_all_windows():
    """Get all visible windows with their titles and process names"""
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    return windows

def find_photoshop_process():
    """Find any running Photoshop processes"""
    photoshop_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if 'photoshop' in proc.info['name'].lower():
                photoshop_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return photoshop_processes

def test_photoshop_launch():
    print("=== Photoshop Launch Test ===\n")
    
    # Check if Photoshop is already running
    print("1. Checking for existing Photoshop processes...")
    existing_processes = find_photoshop_process()
    if existing_processes:
        print("   Found existing Photoshop processes:")
        for proc in existing_processes:
            print(f"   - PID: {proc['pid']}, Name: {proc['name']}")
    else:
        print("   No existing Photoshop processes found")
    
    print("\n2. Current visible windows before launch:")
    windows_before = get_all_windows()
    photoshop_windows_before = [w for w in windows_before if 'photoshop' in w[1].lower() or 'photoshop' in w[2].lower()]
    if photoshop_windows_before:
        for hwnd, title, proc_name, pid in photoshop_windows_before:
            print(f"   - {title} ({proc_name}, PID: {pid})")
    else:
        print("   No Photoshop windows found")
    
    # Launch Photoshop
    print("\n3. Launching Photoshop...")
    photoshop_path = r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe"
    
    if not os.path.exists(photoshop_path):
        print(f"   ERROR: Photoshop not found at {photoshop_path}")
        return
    
    try:
        process = subprocess.Popen(photoshop_path)
        print(f"   Launched with PID: {process.pid}")
    except Exception as e:
        print(f"   ERROR launching: {e}")
        return
    
    # Wait and check for windows periodically
    print("\n4. Monitoring for Photoshop windows...")
    for i in range(30):  # Check for 30 seconds
        time.sleep(1)
        
        # Check processes
        current_processes = find_photoshop_process()
        
        # Check windows
        current_windows = get_all_windows()
        photoshop_windows = [w for w in current_windows if 'photoshop' in w[1].lower() or 'photoshop' in w[2].lower()]
        
        if photoshop_windows:
            print(f"\n   SUCCESS! Found Photoshop window(s) after {i+1} seconds:")
            for hwnd, title, proc_name, pid in photoshop_windows:
                print(f"   - HWND: {hwnd}")
                print(f"     Title: '{title}'")
                print(f"     Process: {proc_name} (PID: {pid})")
                
                # Get window position and size
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    print(f"     Position: {rect}")
                except:
                    print("     Position: Could not get window rect")
            break
        else:
            print(f"   Waiting... ({i+1}/30s) - Processes: {len(current_processes)}")
    
    else:
        print("\n   TIMEOUT: No Photoshop windows found after 30 seconds")
        
        # Show all current processes and windows for debugging
        print("\n   Current Photoshop processes:")
        current_processes = find_photoshop_process()
        for proc in current_processes:
            print(f"   - PID: {proc['pid']}, Name: {proc['name']}, Path: {proc.get('exe', 'N/A')}")
        
        print("\n   All current windows (first 10):")
        all_windows = get_all_windows()
        for i, (hwnd, title, proc_name, pid) in enumerate(all_windows[:10]):
            print(f"   - {title} ({proc_name})")

if __name__ == "__main__":
    test_photoshop_launch()