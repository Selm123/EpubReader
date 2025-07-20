import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
from PIL import Image, ImageTk
import io
import threading
import webbrowser
from pathlib import Path

class EpubReader:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB Reader")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Variables
        self.current_book = None
        self.current_chapter = 0
        self.chapters = []
        self.book_title = ""
        self.book_author = ""
        self.font_size = 12
        self.font_family = "Arial"
        self.dark_mode = False
        self.bg_color = "#ffffff"  # Default white background
        self.text_color = "#000000"  # Default black text
        
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        # Create main menu
        self.create_menu()
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create toolbar
        self.create_toolbar(main_frame)
        
        # Create content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Create sidebar for book info and navigation
        self.create_sidebar(content_frame)
        
        # Create reading area
        self.create_reading_area(content_frame)
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open EPUB", command=self.open_epub, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Increase Font Size", command=self.increase_font_size, accelerator="Ctrl++")
        view_menu.add_command(label="Decrease Font Size", command=self.decrease_font_size, accelerator="Ctrl+-")
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode, accelerator="Ctrl+D")
        view_menu.add_separator()
        view_menu.add_command(label="Customize Colors", command=self.show_color_dialog)
        
        # Navigation menu
        nav_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Navigation", menu=nav_menu)
        nav_menu.add_command(label="Previous Chapter", command=self.previous_chapter, accelerator="Ctrl+Left")
        nav_menu.add_command(label="Next Chapter", command=self.next_chapter, accelerator="Ctrl+Right")
        nav_menu.add_command(label="Table of Contents", command=self.show_toc)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_epub())
        self.root.bind('<Control-plus>', lambda e: self.increase_font_size())
        self.root.bind('<Control-minus>', lambda e: self.decrease_font_size())
        self.root.bind('<Control-d>', lambda e: self.toggle_dark_mode())
        self.root.bind('<Control-Left>', lambda e: self.previous_chapter())
        self.root.bind('<Control-Right>', lambda e: self.next_chapter())
        
    def create_toolbar(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Open button
        open_btn = ttk.Button(toolbar, text="Open EPUB", command=self.open_epub)
        open_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Navigation buttons
        ttk.Button(toolbar, text="◀ Previous", command=self.previous_chapter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Next ▶", command=self.next_chapter).pack(side=tk.LEFT, padx=(0, 5))
        
        # Font controls
        ttk.Label(toolbar, text="Font:").pack(side=tk.LEFT, padx=(20, 5))
        font_combo = ttk.Combobox(toolbar, values=["Arial", "Times New Roman", "Georgia", "Verdana", "Courier New"], 
                                 width=12, state="readonly")
        font_combo.set(self.font_family)
        font_combo.pack(side=tk.LEFT, padx=(0, 5))
        font_combo.bind('<<ComboboxSelected>>', self.change_font)
        
        ttk.Label(toolbar, text="Size:").pack(side=tk.LEFT, padx=(10, 5))
        size_combo = ttk.Combobox(toolbar, values=[8, 10, 12, 14, 16, 18, 20, 24, 28, 32], 
                                 width=5, state="readonly")
        size_combo.set(self.font_size)
        size_combo.pack(side=tk.LEFT, padx=(0, 5))
        size_combo.bind('<<ComboboxSelected>>', self.change_font_size)
        
        # Color customization button
        ttk.Button(toolbar, text="🎨 Colors", command=self.show_color_dialog).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Dark mode toggle
        self.dark_btn = ttk.Button(toolbar, text="🌙 Dark Mode", command=self.toggle_dark_mode)
        self.dark_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
    def create_sidebar(self, parent):
        # Create paned window
        self.paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar frame
        sidebar_frame = ttk.Frame(self.paned_window, width=250)
        self.paned_window.add(sidebar_frame, weight=0)
        
        # Book info
        info_frame = ttk.LabelFrame(sidebar_frame, text="Book Information", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.title_label = ttk.Label(info_frame, text="No book loaded", font=("Arial", 12, "bold"))
        self.title_label.pack(anchor=tk.W)
        
        self.author_label = ttk.Label(info_frame, text="", font=("Arial", 10))
        self.author_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Chapter navigation
        nav_frame = ttk.LabelFrame(sidebar_frame, text="Chapters", padding=10)
        nav_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Chapter listbox with scrollbar
        list_frame = ttk.Frame(nav_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chapter_listbox = tk.Listbox(list_frame, font=("Arial", 10))
        chapter_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.chapter_listbox.yview)
        self.chapter_listbox.configure(yscrollcommand=chapter_scrollbar.set)
        
        self.chapter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chapter_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.chapter_listbox.bind('<<ListboxSelect>>', self.on_chapter_select)
        
    def create_reading_area(self, parent):
        # Reading area frame
        reading_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(reading_frame, weight=1)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(reading_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=(self.font_family, self.font_size),
            padx=20,
            pady=20,
            state=tk.DISABLED
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse wheel for scrolling
        self.text_widget.bind('<MouseWheel>', self.on_mousewheel)
        
    def create_status_bar(self):
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def open_epub(self):
        file_path = filedialog.askopenfilename(
            title="Open EPUB File",
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_epub(file_path)
            
    def load_epub(self, file_path):
        try:
            self.status_bar.config(text="Loading EPUB...")
            self.root.update()
            
            # Load EPUB in a separate thread to avoid freezing
            def load_thread():
                try:
                    book = epub.read_epub(file_path)
                    
                    # Get book metadata
                    title = book.get_metadata('DC', 'title')
                    author = book.get_metadata('DC', 'creator')
                    
                    self.book_title = title[0][0] if title else "Unknown Title"
                    self.book_author = author[0][0] if author else "Unknown Author"
                    
                    # Extract chapters
                    self.chapters = []
                    for item in book.get_items():
                        if item.get_type() == ebooklib.ITEM_DOCUMENT:
                            soup = BeautifulSoup(item.get_content(), 'html.parser')
                            # Remove script and style elements
                            for script in soup(["script", "style"]):
                                script.decompose()
                            
                            # Get text content
                            text = soup.get_text()
                            # Clean up text
                            lines = (line.strip() for line in text.splitlines())
                            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                            text = ' '.join(chunk for chunk in chunks if chunk)
                            
                            if text.strip():
                                self.chapters.append({
                                    'title': item.get_name() or f"Chapter {len(self.chapters) + 1}",
                                    'content': text
                                })
                    
                    # Update UI in main thread
                    self.root.after(0, self.update_ui_after_load)
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load EPUB: {str(e)}"))
                    self.root.after(0, lambda: self.status_bar.config(text="Error loading EPUB"))
            
            threading.Thread(target=load_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open EPUB: {str(e)}")
            self.status_bar.config(text="Error opening EPUB")
            
    def update_ui_after_load(self):
        # Update book info
        self.title_label.config(text=self.book_title)
        self.author_label.config(text=f"by {self.book_author}")
        
        # Update chapter list
        self.chapter_listbox.delete(0, tk.END)
        for i, chapter in enumerate(self.chapters):
            self.chapter_listbox.insert(tk.END, chapter['title'])
        
        # Load first chapter
        if self.chapters:
            self.current_chapter = 0
            self.load_chapter(0)
        
        self.status_bar.config(text=f"Loaded: {self.book_title}")
        
    def load_chapter(self, chapter_index):
        if 0 <= chapter_index < len(self.chapters):
            self.current_chapter = chapter_index
            
            # Update listbox selection
            self.chapter_listbox.selection_clear(0, tk.END)
            self.chapter_listbox.selection_set(chapter_index)
            self.chapter_listbox.see(chapter_index)
            
            # Load content
            chapter = self.chapters[chapter_index]
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(1.0, chapter['content'])
            self.text_widget.config(state=tk.DISABLED)
            
            # Update status
            self.status_bar.config(text=f"Chapter {chapter_index + 1} of {len(self.chapters)}: {chapter['title']}")
            
    def on_chapter_select(self, event):
        selection = self.chapter_listbox.curselection()
        if selection:
            self.load_chapter(selection[0])
            
    def previous_chapter(self):
        if self.current_chapter > 0:
            self.load_chapter(self.current_chapter - 1)
            
    def next_chapter(self):
        if self.current_chapter < len(self.chapters) - 1:
            self.load_chapter(self.current_chapter + 1)
            
    def increase_font_size(self):
        self.font_size = min(32, self.font_size + 2)
        self.update_font()
        
    def decrease_font_size(self):
        self.font_size = max(8, self.font_size - 2)
        self.update_font()
        
    def change_font_size(self, event):
        self.font_size = int(event.widget.get())
        self.update_font()
        
    def change_font(self, event):
        self.font_family = event.widget.get()
        self.update_font()
        
    def update_font(self):
        self.text_widget.config(font=(self.font_family, self.font_size))
        
    def update_colors(self):
        """Update text widget colors"""
        if not self.dark_mode:
            self.text_widget.configure(
                bg=self.bg_color,
                fg=self.text_color,
                insertbackground=self.text_color
            )
        
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        
    def apply_theme(self):
        if self.dark_mode:
            # Dark theme
            self.root.configure(bg='#2b2b2b')
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure dark colors
            style.configure('TFrame', background='#2b2b2b')
            style.configure('TLabel', background='#2b2b2b', foreground='#ffffff')
            style.configure('TButton', background='#404040', foreground='#ffffff')
            style.configure('TLabelframe', background='#2b2b2b', foreground='#ffffff')
            style.configure('TLabelframe.Label', background='#2b2b2b', foreground='#ffffff')
            
            # Text widget dark theme
            self.text_widget.configure(
                bg='#1e1e1e',
                fg='#ffffff',
                insertbackground='#ffffff',
                selectbackground='#404040',
                selectforeground='#ffffff'
            )
            
            # Listbox dark theme
            self.chapter_listbox.configure(
                bg='#1e1e1e',
                fg='#ffffff',
                selectbackground='#404040',
                selectforeground='#ffffff'
            )
            
            self.dark_btn.configure(text="☀️ Light Mode")
            
        else:
            # Light theme
            self.root.configure(bg='#f0f0f0')
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure light colors
            style.configure('TFrame', background='#f0f0f0')
            style.configure('TLabel', background='#f0f0f0', foreground='#000000')
            style.configure('TButton', background='#e0e0e0', foreground='#000000')
            style.configure('TLabelframe', background='#f0f0f0', foreground='#000000')
            style.configure('TLabelframe.Label', background='#f0f0f0', foreground='#000000')
            
            # Text widget light theme
            self.text_widget.configure(
                bg=self.bg_color,
                fg=self.text_color,
                insertbackground=self.text_color,
                selectbackground='#0078d4',
                selectforeground='#ffffff'
            )
            
            # Listbox light theme
            self.chapter_listbox.configure(
                bg='#ffffff',
                fg='#000000',
                selectbackground='#0078d4',
                selectforeground='#ffffff'
            )
            
            self.dark_btn.configure(text="🌙 Dark Mode")
            
    def on_mousewheel(self, event):
        self.text_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
    def show_toc(self):
        if not self.chapters:
            messagebox.showinfo("Table of Contents", "No book loaded")
            return
            
        toc_window = tk.Toplevel(self.root)
        toc_window.title("Table of Contents")
        toc_window.geometry("400x500")
        toc_window.transient(self.root)
        toc_window.grab_set()
        
        # Create listbox for TOC
        listbox = tk.Listbox(toc_window, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(toc_window, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Populate TOC
        for i, chapter in enumerate(self.chapters):
            listbox.insert(tk.END, f"{i+1}. {chapter['title']}")
            
        def on_toc_select(event):
            selection = listbox.curselection()
            if selection:
                toc_window.destroy()
                self.load_chapter(selection[0])
                
        listbox.bind('<Double-Button-1>', on_toc_select)
        
    def show_color_dialog(self):
        """Show color customization dialog"""
        if self.dark_mode:
            messagebox.showinfo("Color Customization", 
                              "Color customization is not available in dark mode.\n"
                              "Please switch to light mode first.")
            return
            
        color_window = tk.Toplevel(self.root)
        color_window.title("Customize Colors")
        color_window.geometry("400x300")
        color_window.transient(self.root)
        color_window.grab_set()
        color_window.resizable(False, False)
        
        # Center the window
        color_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Main frame
        main_frame = ttk.Frame(color_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Customize Reading Colors", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Background color section
        bg_frame = ttk.LabelFrame(main_frame, text="Background Color", padding=10)
        bg_frame.pack(fill=tk.X, pady=(0, 15))
        
        bg_color_var = tk.StringVar(value=self.bg_color)
        
        def choose_bg_color():
            color = tk.colorchooser.askcolor(title="Choose Background Color", color=self.bg_color)
            if color[1]:
                bg_color_var.set(color[1])
                bg_preview.configure(bg=color[1])
        
        bg_button = ttk.Button(bg_frame, text="Choose Background Color", command=choose_bg_color)
        bg_button.pack(side=tk.LEFT, padx=(0, 10))
        
        bg_preview = tk.Label(bg_frame, text="Preview", width=10, height=2, relief=tk.SUNKEN)
        bg_preview.configure(bg=self.bg_color)
        bg_preview.pack(side=tk.LEFT)
        
        # Text color section
        text_frame = ttk.LabelFrame(main_frame, text="Text Color", padding=10)
        text_frame.pack(fill=tk.X, pady=(0, 15))
        
        text_color_var = tk.StringVar(value=self.text_color)
        
        def choose_text_color():
            color = tk.colorchooser.askcolor(title="Choose Text Color", color=self.text_color)
            if color[1]:
                text_color_var.set(color[1])
                text_preview.configure(fg=color[1])
        
        text_button = ttk.Button(text_frame, text="Choose Text Color", command=choose_text_color)
        text_button.pack(side=tk.LEFT, padx=(0, 10))
        
        text_preview = tk.Label(text_frame, text="Preview", width=10, height=2, relief=tk.SUNKEN, bg="white")
        text_preview.configure(fg=self.text_color)
        text_preview.pack(side=tk.LEFT)
        
        # Preset colors
        preset_frame = ttk.LabelFrame(main_frame, text="Preset Themes", padding=10)
        preset_frame.pack(fill=tk.X, pady=(0, 15))
        
        preset_colors = [
            ("Cream", "#f5f5dc", "#2c2c2c"),
            ("Sepia", "#f4ecd8", "#5c4b37"),
            ("Light Blue", "#e6f3ff", "#2c2c2c"),
            ("Light Green", "#f0f8f0", "#2c2c2c"),
            ("Light Yellow", "#fffff0", "#2c2c2c"),
            ("Reset to Default", "#ffffff", "#000000")
        ]
        
        def apply_preset(bg_color, text_color):
            bg_color_var.set(bg_color)
            text_color_var.set(text_color)
            bg_preview.configure(bg=bg_color)
            text_preview.configure(fg=text_color)
        
        # Create preset buttons in a grid
        for i, (name, bg_color, text_color) in enumerate(preset_colors):
            row = i // 3
            col = i % 3
            btn = ttk.Button(preset_frame, text=name, 
                           command=lambda bg=bg_color, text=text_color: apply_preset(bg, text))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Configure grid weights
        for i in range(3):
            preset_frame.columnconfigure(i, weight=1)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def apply_colors():
            self.bg_color = bg_color_var.get()
            self.text_color = text_color_var.get()
            self.update_colors()
            color_window.destroy()
            messagebox.showinfo("Colors Applied", "Reading colors have been updated!")
        
        def cancel():
            color_window.destroy()
        
        ttk.Button(button_frame, text="Apply", command=apply_colors).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT)
        
    def show_about(self):
        about_text = """EPUB Reader v1.0

A simple and elegant EPUB reader for Windows.

Features:
• Open and read EPUB files
• Chapter navigation
• Font size and family customization
• Dark/Light mode toggle
• Custom background and text colors
• Table of contents
• Keyboard shortcuts

Keyboard Shortcuts:
Ctrl+O: Open EPUB
Ctrl++: Increase font size
Ctrl+-: Decrease font size
Ctrl+D: Toggle dark mode
Ctrl+Left: Previous chapter
Ctrl+Right: Next chapter

Created with Python and tkinter"""
        
        messagebox.showinfo("About EPUB Reader", about_text)

def main():
    root = tk.Tk()
    app = EpubReader(root)
    root.mainloop()

if __name__ == "__main__":
    main() 