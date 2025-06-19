#!/usr/bin/env python3
"""
Video Transcription Tool - Run Script
This script starts the Streamlit application
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "streamlit",
        "speech_recognition", 
        "pydub",
        "moviepy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n🔧 Please run the installation script first:")
        print("   python install.py")
        print("\nOr install manually:")
        print("   pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_app_file():
    """Check if the main app file exists"""
    if not os.path.exists("app.py"):
        print("❌ app.py file not found!")
        print("Please make sure you have the main application file in the current directory.")
        return False
    return True

def run_streamlit():
    """Run the Streamlit application"""
    try:
        print("🚀 Starting Video Transcription Tool...")
        print("🌐 The application will open in your web browser")
        print("⏹️  Press Ctrl+C to stop the application")
        print("=" * 50)
        
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        print("Please check if Streamlit is properly installed:")
        print("   pip install streamlit")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main function"""
    print("🎬 Video Transcription Tool")
    print("=" * 40)
    
    # Check if dependencies are installed
    if not check_dependencies():
        return
    
    # Check if app file exists
    if not check_app_file():
        return
    
    # Run the application
    run_streamlit()

if __name__ == "__main__":
    main()
