# EPUB Reader

A modern, feature-rich EPUB reader application for Windows built with Python and tkinter.

## Features

- 📖 **EPUB File Support**: Open and read EPUB files with full text extraction
- 📚 **Chapter Navigation**: Easy navigation between chapters with sidebar and keyboard shortcuts
- 🎨 **Customizable Reading Experience**: 
  - Adjustable font size and family
  - Dark/Light mode toggle
  - Custom background and text colors
  - Preset color themes (Cream, Sepia, Light Blue, etc.)
  - Comfortable reading layout
- ⌨️ **Keyboard Shortcuts**: Quick access to common functions
- 📋 **Table of Contents**: Dedicated TOC window for easy chapter selection
- 📱 **Responsive Design**: Resizable window with minimum size constraints
- 🎯 **Modern UI**: Clean, intuitive interface with proper theming

## Screenshots

The application features a clean, modern interface with:
- Toolbar with quick access buttons
- Sidebar showing book information and chapter list
- Main reading area with customizable text display
- Status bar with current chapter information

## Installation

### Prerequisites

- Python 3.7 or higher
- Windows 10/11

### Setup

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd EpubReader
   ```

2. **Install required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python epub_reader.py
   ```

## Usage

### Opening an EPUB File

1. Click the "Open EPUB" button in the toolbar, or
2. Use the File menu → "Open EPUB", or
3. Press `Ctrl+O`

### Navigation

- **Previous Chapter**: Click "◀ Previous" button or press `Ctrl+Left`
- **Next Chapter**: Click "Next ▶" button or press `Ctrl+Right`
- **Chapter List**: Click on any chapter in the sidebar
- **Table of Contents**: Use Navigation menu → "Table of Contents"

### Customization

- **Font Size**: Use the size dropdown or press `Ctrl++`/`Ctrl+-`
- **Font Family**: Select from the font dropdown (Arial, Times New Roman, Georgia, Verdana, Courier New)
- **Dark Mode**: Click the "🌙 Dark Mode" button or press `Ctrl+D`
- **Custom Colors**: Click the "🎨 Colors" button to customize background and text colors
  - Choose custom colors using the color picker
  - Use preset themes: Cream, Sepia, Light Blue, Light Green, Light Yellow
  - Reset to default white background and black text

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open EPUB file |
| `Ctrl++` | Increase font size |
| `Ctrl+-` | Decrease font size |
| `Ctrl+D` | Toggle dark/light mode |
| `Ctrl+Left` | Previous chapter |
| `Ctrl+Right` | Next chapter |

## Features in Detail

### EPUB Parsing
- Extracts text content from EPUB files
- Handles HTML content with proper text cleaning
- Displays book metadata (title, author)
- Supports chapter-based navigation

### Reading Experience
- Word-wrapped text display
- Scrollable content with mouse wheel support
- Comfortable padding and margins
- Non-editable text area to prevent accidental changes

### User Interface
- Modern, responsive design
- Resizable window with minimum size constraints
- Proper theming for both light and dark modes
- Customizable background and text colors
- Intuitive layout with clear visual hierarchy

### Performance
- Asynchronous EPUB loading to prevent UI freezing
- Efficient text processing and display
- Memory-conscious chapter management

## Technical Details

### Dependencies

- **ebooklib**: EPUB file parsing and manipulation
- **BeautifulSoup4**: HTML content parsing
- **Pillow**: Image handling (for future enhancements)
- **tkinter**: GUI framework (included with Python)

### Architecture

The application is built using object-oriented design with the following main components:

- **EpubReader**: Main application class
- **UI Components**: Menu, toolbar, sidebar, reading area, status bar
- **EPUB Processing**: File loading, text extraction, chapter management
- **Theme Management**: Dark/light mode switching

## Future Enhancements

Potential features for future versions:
- Bookmarking system
- Reading progress tracking
- Search functionality
- Text highlighting
- Note-taking capabilities
- Library management
- Export to other formats
- Reading statistics
- Color scheme persistence
- More preset themes

## Troubleshooting

### Common Issues

1. **"No module named 'ebooklib'"**
   - Solution: Run `pip install -r requirements.txt`

2. **EPUB file won't open**
   - Ensure the file is a valid EPUB format
   - Check file permissions
   - Try a different EPUB file

3. **Text appears garbled**
   - Some EPUB files may have encoding issues
   - Try opening the file in another EPUB reader to verify

4. **Application is slow**
   - Large EPUB files may take time to load
   - The loading process runs in a background thread to prevent freezing

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is open source and available under the MIT License.

## Support

If you encounter any issues or have questions, please:
1. Check the troubleshooting section above
2. Search existing issues
3. Create a new issue with detailed information about your problem

---

**Enjoy reading with EPUB Reader! 📚** 