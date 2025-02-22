import os
import subprocess
import sys

def run_command(command):
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"? Error: {e.stderr}")
        sys.exit(1)

# Check Python version
if sys.version_info == (3, 10):
    print("Python 3.10 is required.")
    sys.exit(1)

# Install Tesseract OCR if not installed
try:
    run_command("setx TESSDATA_PREFIX \"C:\\Program Files\\Tesseract-OCR\\tessdata\"")
    run_command('setx PATH "C:\Program Files\Tesseract-OCR;%PATH%"')

    if not os.path.exists("C:\\Program Files\\Tesseract-OCR"):
        print("Tesseract OCR is not installed.")
        tesseract_url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"

        # Force PowerShell to use TLS 1.2+ for downloading
        run_command(f'powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri \\"{tesseract_url}\\" -OutFile \\"tesseract-installer.exe\\""')

        run_command("start /wait tesseract-installer.exe /S")
        os.remove("tesseract-installer.exe")
        run_command("setx TESSDATA_PREFIX \"C:\\Program Files\\Tesseract-OCR\\tessdata\"")
        run_command('setx PATH "C:\Program Files\Tesseract-OCR;%PATH%"')

    print("? Tesseract OCR installation complete!")

    # Download Farsi language data for Tesseract
    tessdata_path = "C:\\Program Files\\Tesseract-OCR\\tessdata"
#    if not os.path.exists(os.path.join(tessdata_path, "fas.traineddata")):
#        print("Downloading Farsi language data (fas.traineddata)...")
#        farsi_url = "https://github.com/tesseract-ocr/tessdata/raw/master/fas.traineddata"
        
        # Force PowerShell to use TLS 1.2+ for downloading
#        run_command(f'powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri \\"{farsi_url}\\" -OutFile \\"{tessdata_path}\\fas.traineddata\\""')
        
 #   print("? Farsi language data downloaded and installed!")

except Exception as e:
    print(f"? Error installing Tesseract OCR: {e}")
    sys.exit(1)

# Install Microsoft C++ Build Tools if not installed
vs_build_tools_url = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
try:
    # Check if MSVC is installed by looking for cl.exe in PATH
    msbuild_check = subprocess.run("where cl", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if msbuild_check.returncode != 0:
        print("Microsoft C++ Build Tools are not installed.")
        
        # Download and install MSVC Build Tools
        run_command(f'powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri \\"{vs_build_tools_url}\\" -OutFile \\"vs_BuildTools.exe\\""')
        
        run_command("start /wait vs_BuildTools.exe --quiet --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.CMake.Project --add Microsoft.VisualStudio.Component.Windows10SDK.20348")
        os.remove("vs_BuildTools.exe")
        print("? MSVC installation complete! Restart your system before proceeding.")
    else:
        print("? MSVC Build Tools are already installed!")
except Exception as e:
    print(f"? Error installing MSVC: {e}")
    sys.exit(1)

# Create virtual environment and install dependencies
try:
    # Create virtual environment
    run_command("python -m venv venv")

    # Install required dependencies
    print("Installing dependencies from requirements.txt...")
    run_command(r"venv\Scripts\python.exe -m pip install -r requirements.txt")

    print("? Installation completed! You can now run the project with:")
    print("python main.py")
except Exception as e:
    print(f"? Error during virtual environment or dependency installation: {e}")
    sys.exit(1)
