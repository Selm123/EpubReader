import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
import json
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
        # Load settings or use defaults
        self.settings_file = "epub_reader_settings.json"
        self.load_settings()
        
        # Initialize reading session data
        self.current_book_path = ""
        self.current_chapter = 0
        self.chapters = []
        self.book_title = ""
        self.book_author = ""
        
        self.setup_ui()
        self.apply_theme()
        
        # Bind window close event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        
        # Restore sidebar width after a short delay to ensure UI is ready
        self.root.after(100, self.restore_sidebar_width)
        
        # Auto-load last book if enabled
        if self.settings.get("auto_load_last_book", True):
            self.root.after(500, self.auto_load_last_book)
        
    def load_settings(self):
        """Load settings from JSON file or use defaults"""
        default_settings = {
            "font_size": 12,
            "font_family": "Georgia",
            "dark_mode": False,
            "bg_color": "#f5f5dc",
            "text_color": "#2c2c2c",
            "two_page_mode": True,
            "window_width": 1200,
            "window_height": 800,
            "sidebar_width": 250,
            "last_book_path": "",
            "last_chapter": 0,
            "auto_load_last_book": True
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # Merge saved settings with defaults (in case new settings were added)
                    for key, value in default_settings.items():
                        if key not in saved_settings:
                            saved_settings[key] = value
                    self.settings = saved_settings
                print(f"✅ Settings loaded from {self.settings_file}")
            else:
                self.settings = default_settings
                print("📝 Using default settings")
        except Exception as e:
            print(f"❌ Error loading settings: {e}")
            self.settings = default_settings
        
        # Apply settings to instance variables
        self.font_size = self.settings["font_size"]
        self.font_family = self.settings["font_family"]
        self.dark_mode = self.settings["dark_mode"]
        self.bg_color = self.settings["bg_color"]
        self.text_color = self.settings["text_color"]
        self.two_page_mode = self.settings["two_page_mode"]
        self.highlights = {}  # Store text highlights
        
        # Set window size
        window_width = self.settings.get("window_width", 1200)
        window_height = self.settings.get("window_height", 800)
        self.root.geometry(f"{window_width}x{window_height}")
        
    def restore_sidebar_width(self):
        """Restore the saved sidebar width after UI is created"""
        if hasattr(self, 'paned_window') and 'sidebar_width' in self.settings:
            try:
                self.paned_window.sashpos(0, self.settings["sidebar_width"])
            except:
                pass  # Ignore errors if paned window isn't ready yet
        
    def save_settings(self):
        """Save current settings to JSON file"""
        try:
            # Update settings with current values
            self.settings.update({
                "font_size": self.font_size,
                "font_family": self.font_family,
                "dark_mode": self.dark_mode,
                "bg_color": self.bg_color,
                "text_color": self.text_color,
                "two_page_mode": self.two_page_mode,
                "window_width": self.root.winfo_width(),
                "window_height": self.root.winfo_height(),
                "sidebar_width": self.paned_window.sashpos(0) if hasattr(self, 'paned_window') else 250,
                "last_book_path": self.current_book_path,
                "last_chapter": self.current_chapter,
                "auto_load_last_book": self.settings.get("auto_load_last_book", True)
            })
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            print(f"💾 Settings saved to {self.settings_file}")
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
            messagebox.showerror("Settings Error", f"Failed to save settings: {e}")
            
    def auto_load_last_book(self):
        """Automatically load the last opened book and position"""
        last_book_path = self.settings.get("last_book_path", "")
        last_chapter = self.settings.get("last_chapter", 0)
        
        if last_book_path and os.path.exists(last_book_path):
            try:
                print(f"📖 Auto-loading last book: {last_book_path}")
                self.status_bar.config(text="Loading last book...")
                
                # Load the book
                self.load_epub(last_book_path)
                
                # After book loads, restore the chapter position
                def restore_position():
                    if self.chapters and 0 <= last_chapter < len(self.chapters):
                        self.current_chapter = last_chapter
                        self.load_chapter(last_chapter)
                        self.status_bar.config(text=f"Restored to chapter {last_chapter + 1}: {self.chapters[last_chapter]['title']}")
                        print(f"✅ Restored to chapter {last_chapter + 1}")
                    else:
                        self.status_bar.config(text="Book loaded, starting from beginning")
                        print("📖 Starting from beginning (invalid chapter position)")
                
                # Wait a bit for the book to load, then restore position
                self.root.after(1000, restore_position)
                
            except Exception as e:
                print(f"❌ Error auto-loading last book: {e}")
                self.status_bar.config(text="Failed to load last book")
        else:
            print("📝 No last book to load or file not found")
            self.status_bar.config(text="Ready - No previous book found")
        
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
        
        # Create reading area with two-page layout
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
        file_menu.add_command(label="Exit", command=self.on_exit)
        
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
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Save Settings", command=self.save_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Toggle Auto-load Last Book", command=self.toggle_auto_load)
        settings_menu.add_command(label="Show Reading Session", command=self.show_reading_session)
        settings_menu.add_command(label="Reset to Defaults", command=self.reset_settings)
        
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
        # Reading area frame with book-like background
        reading_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(reading_frame, weight=1)
        
        # Create book container with background
        self.book_container = tk.Frame(reading_frame, bg='#2b2b2b')  # Dark background like desk
        self.book_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Book pages container
        self.pages_container = tk.Frame(self.book_container, bg='#2b2b2b')
        self.pages_container.pack(expand=True)
        
        # Create two-page layout
        self.create_two_page_layout()
        
        # Progress indicator
        self.progress_label = tk.Label(self.book_container, text="", 
                                      bg='#2b2b2b', fg='#ffffff', font=("Arial", 10))
        self.progress_label.pack(side=tk.BOTTOM, pady=10)
        
    def create_two_page_layout(self):
        """Create the two-page book layout"""
        # Left page
        self.left_page = tk.Frame(self.pages_container, 
                                 bg=self.bg_color, 
                                 relief=tk.RAISED, 
                                 bd=2,
                                 width=400, height=600)
        self.left_page.pack(side=tk.LEFT, padx=(0, 10), pady=20)
        self.left_page.pack_propagate(False)
        
        # Right page
        self.right_page = tk.Frame(self.pages_container, 
                                  bg=self.bg_color, 
                                  relief=tk.RAISED, 
                                  bd=2,
                                  width=400, height=600)
        self.right_page.pack(side=tk.LEFT, padx=(10, 0), pady=20)
        self.right_page.pack_propagate(False)
        
        # Left page content
        self.left_text = tk.Text(self.left_page, 
                                wrap=tk.WORD,
                                font=(self.font_family, self.font_size),
                                bg=self.bg_color,
                                fg=self.text_color,
                                relief=tk.FLAT,
                                padx=30,
                                pady=30,
                                state=tk.DISABLED,
                                cursor="ibeam")
        self.left_text.pack(fill=tk.BOTH, expand=True)
        
        # Right page content
        self.right_text = tk.Text(self.right_page, 
                                 wrap=tk.WORD,
                                 font=(self.font_family, self.font_size),
                                 bg=self.bg_color,
                                 fg=self.text_color,
                                 relief=tk.FLAT,
                                 padx=30,
                                 pady=30,
                                 state=tk.DISABLED,
                                 cursor="ibeam")
        self.right_text.pack(fill=tk.BOTH, expand=True)
        
        # Bind events for text interaction
        self.left_text.bind('<Button-1>', self.on_text_click)
        self.right_text.bind('<Button-1>', self.on_text_click)
        self.left_text.bind('<ButtonRelease-1>', self.on_text_release)
        self.right_text.bind('<ButtonRelease-1>', self.on_text_release)
        
        # Bind right-click for page navigation
        self.left_text.bind('<Button-3>', self.on_right_click)
        self.right_text.bind('<Button-3>', self.on_right_click)
        
        # Create context toolbar (initially hidden)
        self.create_context_toolbar()
        
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
            
            # Save the book path
            self.current_book_path = file_path
            
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
                    
                    # Save settings after successful load
                    self.root.after(0, self.save_settings)
                    
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
        """Load a specific chapter"""
        if 0 <= chapter_index < len(self.chapters):
            self.current_chapter = chapter_index
            
            # Update listbox selection
            self.chapter_listbox.selection_clear(0, tk.END)
            self.chapter_listbox.selection_set(chapter_index)
            self.chapter_listbox.see(chapter_index)
            
            # Load content into two-page layout
            chapter = self.chapters[chapter_index]
            self.load_content_to_pages(chapter['content'], chapter['title'])
            
            # Update status and progress
            auto_save_status = " | Auto-saved" if self.settings.get("auto_load_last_book", True) else ""
            self.status_bar.config(text=f"Chapter {chapter_index + 1} of {len(self.chapters)}: {chapter['title']} | Right-click to go to next page{auto_save_status}")
            self.update_progress()
            
            # Save current position
            self.save_settings()
        
    def load_content_to_pages(self, content, title):
        """Load content into the two-page layout"""
        # Clear both pages
        self.left_text.config(state=tk.NORMAL)
        self.right_text.config(state=tk.NORMAL)
        self.left_text.delete(1.0, tk.END)
        self.right_text.delete(1.0, tk.END)
        
        # Add title to left page
        self.left_text.insert(tk.END, f"{self.book_author}\n\n", "title")
        self.left_text.insert(tk.END, f"{title}\n\n", "subtitle")
        
        # Split content between pages
        words = content.split()
        mid_point = len(words) // 2
        
        # Left page content
        left_content = " ".join(words[:mid_point])
        self.left_text.insert(tk.END, left_content)
        
        # Right page content
        right_content = " ".join(words[mid_point:])
        self.right_text.insert(tk.END, right_content)
        
        # Configure tags for styling
        self.left_text.tag_configure("title", font=(self.font_family, self.font_size + 4, "bold"), 
                                    foreground=self.text_color, justify=tk.CENTER)
        self.left_text.tag_configure("subtitle", font=(self.font_family, self.font_size + 2, "bold"), 
                                    foreground=self.text_color, justify=tk.CENTER)
        
        self.right_text.tag_configure("title", font=(self.font_family, self.font_size + 4, "bold"), 
                                     foreground=self.text_color, justify=tk.CENTER)
        self.right_text.tag_configure("subtitle", font=(self.font_family, self.font_size + 2, "bold"), 
                                     foreground=self.text_color, justify=tk.CENTER)
        
        # Disable editing
        self.left_text.config(state=tk.DISABLED)
        self.right_text.config(state=tk.DISABLED)
        
    def update_progress(self):
        """Update the progress indicator"""
        if self.chapters:
            progress = (self.current_chapter + 1) / len(self.chapters) * 100
            self.progress_label.config(text=f"location {self.current_chapter + 1} of {len(self.chapters)} ({progress:.0f}%)")
            
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
        self.save_settings()
        
    def decrease_font_size(self):
        self.font_size = max(8, self.font_size - 2)
        self.update_font()
        self.save_settings()
        
    def change_font_size(self, event):
        self.font_size = int(event.widget.get())
        self.update_font()
        self.save_settings()
        
    def change_font(self, event):
        self.font_family = event.widget.get()
        self.update_font()
        self.save_settings()
        
    def update_font(self):
        # Update both text widgets
        self.left_text.config(font=(self.font_family, self.font_size))
        self.right_text.config(font=(self.font_family, self.font_size))
        
        # Update text tags with new font sizes
        self.left_text.tag_configure("title", font=(self.font_family, self.font_size + 4, "bold"))
        self.left_text.tag_configure("subtitle", font=(self.font_family, self.font_size + 2, "bold"))
        self.right_text.tag_configure("title", font=(self.font_family, self.font_size + 4, "bold"))
        self.right_text.tag_configure("subtitle", font=(self.font_family, self.font_size + 2, "bold"))
        
    def update_colors(self):
        """Update text widget colors"""
        if not self.dark_mode:
            # Update page backgrounds
            self.left_page.configure(bg=self.bg_color)
            self.right_page.configure(bg=self.bg_color)
            
            # Update text widgets
            self.left_text.configure(
                bg=self.bg_color,
                fg=self.text_color,
                insertbackground=self.text_color
            )
            self.right_text.configure(
                bg=self.bg_color,
                fg=self.text_color,
                insertbackground=self.text_color
            )
            
            # Update text tags
            self.left_text.tag_configure("title", foreground=self.text_color)
            self.left_text.tag_configure("subtitle", foreground=self.text_color)
            self.right_text.tag_configure("title", foreground=self.text_color)
            self.right_text.tag_configure("subtitle", foreground=self.text_color)
            
            # Force update the display
            self.left_text.update_idletasks()
            self.right_text.update_idletasks()
        
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_settings()
        
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
            
            # Page dark theme
            self.left_page.configure(bg='#1e1e1e')
            self.right_page.configure(bg='#1e1e1e')
            
            # Text widget dark theme
            self.left_text.configure(
                bg='#1e1e1e',
                fg='#ffffff',
                insertbackground='#ffffff',
                selectbackground='#404040',
                selectforeground='#ffffff'
            )
            self.right_text.configure(
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
            
            # Page light theme
            self.left_page.configure(bg=self.bg_color)
            self.right_page.configure(bg=self.bg_color)
            
            # Text widget light theme
            self.left_text.configure(
                bg=self.bg_color,
                fg=self.text_color,
                insertbackground=self.text_color,
                selectbackground='#0078d4',
                selectforeground='#ffffff'
            )
            self.right_text.configure(
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
        # Handle mousewheel for page navigation
        if event.delta > 0:
            self.previous_chapter()
        else:
            self.next_chapter()
        
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
                # Apply immediately when color is chosen
                self.bg_color = color[1]
                self.update_colors()
                self.save_settings()
        
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
                # Apply immediately when color is chosen
                self.text_color = color[1]
                self.update_colors()
                self.save_settings()
        
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
            # Apply immediately when preset is selected
            self.bg_color = bg_color
            self.text_color = text_color
            self.update_colors()
            self.save_settings()
        
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
            self.save_settings()
            color_window.destroy()
            messagebox.showinfo("Colors Applied", "Reading colors have been updated!")
        
        def cancel():
            color_window.destroy()
        
        ttk.Button(button_frame, text="Apply", command=apply_colors).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT)
        
    def on_exit(self):
        """Handle application exit - save settings before closing"""
        self.save_settings()
        self.root.quit()
        
    def reset_settings(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", 
                              "Are you sure you want to reset all settings to defaults?\n"
                              "This will restart the application."):
            try:
                # Remove settings file
                if os.path.exists(self.settings_file):
                    os.remove(self.settings_file)
                    print(f"🗑️ Settings file removed: {self.settings_file}")
                
                messagebox.showinfo("Settings Reset", 
                                  "Settings have been reset to defaults.\n"
                                  "The application will restart.")
                
                # Restart the application
                self.root.after(1000, self.restart_application)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset settings: {e}")
                
    def restart_application(self):
        """Restart the application"""
        self.root.destroy()
        main()
        
    def toggle_auto_load(self):
        """Toggle auto-load last book setting"""
        current_setting = self.settings.get("auto_load_last_book", True)
        new_setting = not current_setting
        self.settings["auto_load_last_book"] = new_setting
        self.save_settings()
        
        status = "enabled" if new_setting else "disabled"
        messagebox.showinfo("Auto-load Setting", 
                          f"Auto-load last book has been {status}.\n"
                          f"This setting will take effect the next time you restart the application.")
        
    def show_reading_session(self):
        """Show current reading session information"""
        if self.current_book_path:
            book_name = os.path.basename(self.current_book_path)
            chapter_info = f"Chapter {self.current_chapter + 1} of {len(self.chapters)}" if self.chapters else "No chapters loaded"
            auto_load_status = "enabled" if self.settings.get("auto_load_last_book", True) else "disabled"
            
            info_text = f"""Current Reading Session:

Book: {book_name}
Title: {self.book_title}
Author: {self.book_author}
Position: {chapter_info}
Auto-load: {auto_load_status}

The app will automatically restore this position when reopened."""
        else:
            info_text = """No book currently loaded.

Open an EPUB file to start reading.
Auto-load is enabled and will remember your position."""
            
        messagebox.showinfo("Reading Session Info", info_text)
        
    def create_context_toolbar(self):
        """Create the context-sensitive toolbar for text interactions"""
        self.context_toolbar = tk.Frame(self.book_container, 
                                       bg='#333333', 
                                       relief=tk.RAISED, 
                                       bd=1)
        
        # Toolbar buttons
        buttons = [
            ("🖍️", "Highlight", self.highlight_text),
            ("📘", "Facebook", self.share_facebook),
            ("🐦", "Twitter", self.share_twitter),
            ("📋", "Copy", self.copy_text),
            ("🔍", "Search", self.search_text),
            ("📖", "Definition", self.get_definition),
            ("📤", "Share", self.share_text)
        ]
        
        for i, (icon, label, command) in enumerate(buttons):
            btn_frame = tk.Frame(self.context_toolbar, bg='#333333')
            btn_frame.pack(side=tk.LEFT, padx=5, pady=5)
            
            btn = tk.Button(btn_frame, text=icon, font=("Arial", 12), 
                           bg='#333333', fg='#ffffff', relief=tk.FLAT,
                           command=command, cursor="hand2")
            btn.pack()
            
            label_widget = tk.Label(btn_frame, text=label, font=("Arial", 8), 
                                   bg='#333333', fg='#ffffff')
            label_widget.pack()
        
        # Initially hidden
        self.context_toolbar.place_forget()
        
    def on_text_click(self, event):
        """Handle text click events"""
        self.hide_context_toolbar()
        
    def on_text_release(self, event):
        """Handle text release events - show context toolbar if text is selected"""
        widget = event.widget
        try:
            selection = widget.tag_ranges(tk.SEL)
            if selection:
                # Show context toolbar near the selection
                self.show_context_toolbar(widget, event.x, event.y)
        except tk.TclError:
            pass  # No selection
            
    def on_right_click(self, event):
        """Handle right-click events for page navigation"""
        # Hide any existing context toolbar
        self.hide_context_toolbar()
        
        # Navigate to next chapter/page
        self.next_chapter()
        
        # Prevent the default context menu
        return "break"
            
    def show_context_toolbar(self, widget, x, y):
        """Show the context toolbar at the specified position"""
        # Convert widget coordinates to screen coordinates
        widget_x = widget.winfo_rootx()
        widget_y = widget.winfo_rooty()
        
        # Position toolbar near the click
        toolbar_x = widget_x + x
        toolbar_y = widget_y + y + 20
        
        self.context_toolbar.place(x=toolbar_x, y=toolbar_y)
        
    def hide_context_toolbar(self):
        """Hide the context toolbar"""
        self.context_toolbar.place_forget()
        
    def highlight_text(self):
        """Highlight selected text"""
        # This would implement text highlighting
        messagebox.showinfo("Highlight", "Text highlighting feature coming soon!")
        
    def share_facebook(self):
        """Share selected text on Facebook"""
        messagebox.showinfo("Share", "Facebook sharing feature coming soon!")
        
    def share_twitter(self):
        """Share selected text on Twitter"""
        messagebox.showinfo("Share", "Twitter sharing feature coming soon!")
        
    def copy_text(self):
        """Copy selected text to clipboard"""
        try:
            # Get the widget that has focus
            focused_widget = self.root.focus_get()
            if hasattr(focused_widget, 'get'):
                selected_text = focused_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                messagebox.showinfo("Copy", "Text copied to clipboard!")
        except tk.TclError:
            messagebox.showinfo("Copy", "No text selected!")
        
    def search_text(self):
        """Search for text in the book"""
        messagebox.showinfo("Search", "Search feature coming soon!")
        
    def get_definition(self):
        """Get definition of selected word"""
        messagebox.showinfo("Definition", "Dictionary lookup feature coming soon!")
        
    def share_text(self):
        """Share selected text"""
        messagebox.showinfo("Share", "General sharing feature coming soon!")
        
    def show_about(self):
        about_text = """EPUB Reader v2.0

A beautiful and immersive EPUB reader for Windows.

Features:
• Open and read EPUB files
• Two-page book layout with realistic styling
• Chapter navigation with progress tracking
• Font size and family customization
• Dark/Light mode toggle
• Custom background and text colors
• Interactive context toolbar
• Text selection and copying
• Table of contents
• Keyboard shortcuts
• Automatic settings persistence
• Auto-save reading position
• Auto-load last book on startup

Keyboard Shortcuts:
Ctrl+O: Open EPUB
Ctrl++: Increase font size
Ctrl+-: Decrease font size
Ctrl+D: Toggle dark mode
Ctrl+Left: Previous chapter
Ctrl+Right: Next chapter

Navigation:
• Right-click on any page to go to next chapter
• Mouse wheel to navigate between chapters

Created with Python and tkinter"""
        
        messagebox.showinfo("About EPUB Reader", about_text)

def main():
    root = tk.Tk()
    app = EpubReader(root)
    root.mainloop()

if __name__ == "__main__":
    main() 