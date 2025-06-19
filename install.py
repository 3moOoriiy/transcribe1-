#!/usr/bin/env python3
"""
Video Transcription Tool - Installation Script
This script automatically installs all required dependencies
"""

import subprocess
import sys
import os
import platform

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    if description:
        print(f"📦 {description}")
    print(f"🔧 Running: {command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print(f"🐍 Python version: {sys.version}")
    
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        sys.exit(1)
    
    print("✅ Python version is compatible")

def upgrade_pip():
    """Upgrade pip to latest version"""
    return run_command(f"{sys.executable} -m pip install --upgrade pip", 
                      "Upgrading pip to latest version")

def install_basic_requirements():
    """Install basic required packages"""
    requirements = [
        "streamlit",
        "SpeechRecognition",
        "pydub",
        "moviepy",
        "requests"
    ]
    
    for package in requirements:
        if not run_command(f"{sys.executable} -m pip install {package}", 
                          f"Installing {package}"):
            print(f"⚠️  Failed to install {package}, continuing...")

def install_pyaudio():
    """Install PyAudio with platform-specific methods"""
    system = platform.system().lower()
    
    print(f"\n📢 Installing PyAudio for {system}...")
    
    if system == "windows":
        # Try pipwin first for Windows
        if run_command(f"{sys.executable} -m pip install pipwin", 
                      "Installing pipwin for Windows"):
            if run_command("pipwin install pyaudio", 
                          "Installing PyAudio via pipwin"):
                return True
        
        # Fallback to regular pip
        return run_command(f"{sys.executable} -m pip install pyaudio", 
                          "Installing PyAudio via pip (fallback)")
    
    elif system == "linux":
        print("🐧 Linux detected - you may need to install system dependencies first:")
        print("   sudo apt-get update")
        print("   sudo apt-get install portaudio19-dev python3-pyaudio")
        print("   Or for CentOS/RHEL: sudo yum install portaudio-devel")
        
        return run_command(f"{sys.executable} -m pip install pyaudio", 
                          "Installing PyAudio")
    
    elif system == "darwin":  # macOS
        print("🍎 macOS detected - you may need to install portaudio first:")
        print("   brew install portaudio")
        
        return run_command(f"{sys.executable} -m pip install pyaudio", 
                          "Installing PyAudio")
    
    else:
        print(f"❓ Unknown system: {system}")
        return run_command(f"{sys.executable} -m pip install pyaudio", 
                          "Installing PyAudio")

def install_ffmpeg():
    """Install or check for FFmpeg"""
    print("\n🎵 Checking FFmpeg installation...")
    
    # Check if FFmpeg is already installed
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg is already installed")
            return True
    except FileNotFoundError:
        pass
    
    system = platform.system().lower()
    
    if system == "windows":
        print("🪟 Windows detected:")
        print("   Please download FFmpeg from: https://ffmpeg.org/download.html")
        print("   Or install via chocolatey: choco install ffmpeg")
        print("   Or install via scoop: scoop install ffmpeg")
    
    elif system == "linux":
        print("🐧 Linux detected:")
        print("   Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("   CentOS/RHEL: sudo yum install ffmpeg")
        print("   Arch: sudo pacman -S ffmpeg")
    
    elif system == "darwin":
        print("🍎 macOS detected:")
        print("   Install via Homebrew: brew install ffmpeg")
        print("   Or via MacPorts: sudo port install ffmpeg")
    
    print("⚠️  FFmpeg is required for video processing!")
    return False

def test_installation():
    """Test if all packages can be imported"""
    print("\n🧪 Testing installation...")
    
    test_packages = [
        ("streamlit", "streamlit"),
        ("speech_recognition", "SpeechRecognition"),
        ("pydub", "pydub"),
        ("moviepy", "moviepy"),
    ]
    
    failed_packages = []
    
    for import_name, package_name in test_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError as e:
            print(f"❌ {package_name}: {e}")
            failed_packages.append(package_name)
    
    if failed_packages:
        print(f"\n⚠️  Failed packages: {', '.join(failed_packages)}")
        print("You may need to install them manually:")
        for package in failed_packages:
            print(f"   pip install {package}")
        return False
    
    print("\n🎉 All packages installed successfully!")
    return True

def create_requirements_file():
    """Create requirements.txt file"""
    requirements_content = """streamlit>=1.28.0
SpeechRecognition>=3.10.0
pydub>=0.25.1
moviepy>=1.0.3
requests>=2.31.0
pyaudio>=0.2.11
"""
    
    try:
        with open("requirements.txt", "w") as f:
            f.write(requirements_content)
        print("✅ Created requirements.txt file")
        return True
    except Exception as e:
        print(f"❌ Failed to create requirements.txt: {e}")
        return False

def main():
    """Main installation function"""
    print("🎬 Video Transcription Tool - Installation Script")
    print("=" * 60)
    
    # Check Python version
    check_python_version()
    
    # Upgrade pip
    upgrade_pip()
    
    # Install basic requirements
    install_basic_requirements()
    
    # Install PyAudio (may require special handling)
    install_pyaudio()
    
    # Check FFmpeg
    install_ffmpeg()
    
    # Test installation
    if test_installation():
        print("\n🎉 Installation completed successfully!")
        print("\n🚀 You can now run the application with:")
        print("   streamlit run app.py")
    else:
        print("\n⚠️  Installation completed with some issues.")
        print("Please check the error messages above and install missing packages manually.")
    
    # Create requirements file
    create_requirements_file()
    
    print("\n📋 Installation Summary:")
    print("  ✅ Basic packages installed")
    print("  ✅ requirements.txt created")
    print("  ⚠️  Make sure FFmpeg is installed for video processing")
    print("  ⚠️  PyAudio may require additional system dependencies")

if __name__ == "__main__":
    main()
