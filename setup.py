#!/usr/bin/env python3
"""
Setup script for EPUB Reader
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True

def main():
    print("EPUB Reader Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return
    
    # Install requirements
    if install_requirements():
        print("\n🎉 Setup completed successfully!")
        print("\nTo run the EPUB Reader:")
        print("1. Double-click 'run_epub_reader.bat' or")
        print("2. Run: python epub_reader.py")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 