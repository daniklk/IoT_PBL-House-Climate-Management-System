import subprocess
import platform

path_encodeir = ""
# Select binary based on platform
system = platform.system()
if system == "Windows":
    path_encodeir = "bin/windows/encodeir.exe"
elif system == "Darwin":  # macOS
    path_encodeir = "bin/macos/encodeir"
else:  # Linux
    path_encodeir = "bin/linux/encodeir"

args = ["NECx2", "7", "7", "2"]
result = subprocess.run([path_encodeir] + args, capture_output=True, text=True)

if result.returncode == 0:
    print("Success")
    print(result.stdout.replace(" ", ""))
else:
    print("Error")
    print(result.stderr)

