#!/usr/bin/env python3
"""
Test script to verify all required modules can be imported
"""

def test_imports():
    """Test importing all required modules"""
    try:
        print("Testing imports...")
        
        import tkinter as tk
        print("✅ tkinter imported successfully")
        
        from tkinter import ttk, filedialog, messagebox, scrolledtext
        print("✅ tkinter widgets imported successfully")
        
        import ebooklib
        from ebooklib import epub
        print("✅ ebooklib imported successfully")
        
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup imported successfully")
        
        from PIL import Image, ImageTk
        print("✅ Pillow imported successfully")
        
        import threading
        print("✅ threading imported successfully")
        
        print("\n🎉 All imports successful! The EPUB reader should work correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports() 