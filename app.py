from flask import Flask, render_template, request, send_file, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import tempfile
import os
import random
import re

app = Flask(__name__)

def load_characters():
    # Use absolute path for PythonAnywhere deployment
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, 'data.txt')
    with open(data_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def select_characters(new_chars, start_char, all_chars):
    """
    Select 50 characters: new chars + old chars for review
    New chars must have indices > 50, review start must be < min(new char indices)
    """
    new_char_list = list(new_chars)
    num_new = len(new_char_list)
    num_old = 50 - num_new
    
    if num_old <= 0:
        return new_char_list[:50]
    
    # Validate all new chars are in data
    new_char_indices = []
    for char in new_char_list:
        if char not in all_chars:
            raise ValueError(f"New character '{char}' not found in data.txt")
        new_char_indices.append(all_chars.index(char))
    
    # Validate all new chars have indices > 50
    min_new_index = min(new_char_indices)
    if min_new_index <= 50:
        raise ValueError(f"All new characters must have indices > 50. Found character at index {min_new_index}")
    
    # Validate start char is in data
    if not start_char:
        raise ValueError("Review starting character is required")
    if start_char not in all_chars:
        raise ValueError(f"Review starting character '{start_char}' not found in data.txt")
    
    start_index = all_chars.index(start_char)
    
    # Validate start index < min new index
    if start_index >= min_new_index:
        raise ValueError(f"Review starting point (index {start_index}) must be less than smallest new character index ({min_new_index})")
    
    # Collect old characters by counting backwards from start_index
    old_chars = []
    current_index = start_index
    
    while len(old_chars) < num_old:
        # Skip if current index is a new character index
        if current_index not in new_char_indices:
            old_chars.append(all_chars[current_index])
        
        # Move to previous index, wrap around if needed
        current_index -= 1
        if current_index < 0:
            current_index = len(all_chars) - 1
            
        # Safety check to prevent infinite loop
        if len(old_chars) == 0 and current_index == start_index:
            raise ValueError("Unable to find enough old characters")
    
    return new_char_list + old_chars[:num_old]

def filter_chinese_characters(text):
    """
    Filter out only Chinese characters from text and remove duplicates
    Returns a string of unique Chinese characters
    """
    # Chinese character Unicode ranges:
    # \u4e00-\u9fff: CJK Unified Ideographs (most common Chinese characters)
    # \u3400-\u4dbf: CJK Extension A
    # \uf900-\ufaff: CJK Compatibility Ideographs
    chinese_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]'
    
    # Find all Chinese characters
    chinese_chars = re.findall(chinese_pattern, text)
    
    # Remove duplicates while preserving order
    unique_chars = []
    seen = set()
    for char in chinese_chars:
        if char not in seen:
            unique_chars.append(char)
            seen.add(char)
    
    return ''.join(unique_chars)

def generate_pdf(characters):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    c = canvas.Canvas(temp_file.name, pagesize=letter)
    
    # Try to register a built-in CID font first (more reliable)
    font_name = "Helvetica"  # fallback
    font_size = 32
    
    try:
        # Try built-in CID fonts for Chinese (more reliable than TTF)
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        font_name = "STSong-Light"
        print("Using built-in STSong-Light CID font")
    except Exception as e:
        print(f"Failed to load STSong-Light: {e}")
        try:
            pdfmetrics.registerFont(UnicodeCIDFont('MSung-Light'))
            font_name = "MSung-Light"
            print("Using built-in MSung-Light CID font")
        except Exception as e:
            print(f"Failed to load MSung-Light: {e}")
            # For PythonAnywhere - use fallback method
            try:
                # Try to use DejaVu Sans which supports some Unicode
                font_name = "Helvetica"
                print("Using Helvetica fallback - Chinese characters may display as boxes")
            except Exception as e:
                print(f"Final fallback failed: {e}")
                font_name = "Helvetica"
    
    if font_name == "Helvetica":
        print("Warning: Using Helvetica fallback - Chinese characters may not display")
    
    c.setFont(font_name, font_size)
    
    width, height = letter  # 612 x 792 points
    margin = 50
    
    # Fixed grid: 5 columns x 10 rows = 50 characters
    chars_per_row = 5
    rows_per_page = 10
    
    # Calculate character cell dimensions to fit the grid
    cell_width = (width - 2 * margin) / chars_per_row
    cell_height = (height - 2 * margin) / rows_per_page
    
    x_start = margin
    y_start = height - margin - cell_height
    
    chars_per_page = chars_per_row * rows_per_page  # 50 characters per page
    
    for i, char in enumerate(characters):
        page_num = i // chars_per_page
        char_on_page = i % chars_per_page
        row = char_on_page // chars_per_row
        col = char_on_page % chars_per_row
        
        # Check if we need a new page
        if i > 0 and char_on_page == 0:
            c.showPage()
            c.setFont(font_name, font_size)
            
        x = x_start + col * cell_width
        y = y_start - row * cell_height
        
        # Draw cell border
        c.rect(x, y, cell_width, cell_height)
        
        # Draw character centered in cell
        try:
            # For Chinese characters with Helvetica fallback, try to encode properly
            if font_name == "Helvetica":
                # Try to draw the character, fallback to placeholder if it fails
                try:
                    # Test if character can be encoded
                    char.encode('latin-1')
                    text_width = c.stringWidth(char, font_name, font_size)
                    x_centered = x + (cell_width - text_width) / 2
                    y_centered = y + cell_height/2 - font_size/3
                    c.drawString(x_centered, y_centered, char)
                except UnicodeEncodeError:
                    # Character can't be encoded in latin-1, draw placeholder
                    x_centered = x + cell_width/2 - 5
                    y_centered = y + cell_height/2 - 5
                    c.setFont("Helvetica", 16)
                    c.drawString(x_centered, y_centered, "□")
                    c.setFont(font_name, font_size)  # Reset font
            else:
                # Using CID font, should work fine
                text_width = c.stringWidth(char, font_name, font_size)
                x_centered = x + (cell_width - text_width) / 2
                y_centered = y + cell_height/2 - font_size/3
                c.drawString(x_centered, y_centered, char)
        except Exception as e:
            print(f"Error drawing character '{char}': {e}")
            # Draw a placeholder
            x_centered = x + cell_width/2 - 5
            y_centered = y + cell_height/2 - 5
            c.setFont("Helvetica", 16)
            c.drawString(x_centered, y_centered, "□")
            c.setFont(font_name, font_size)  # Reset font
    
    c.save()
    return temp_file.name

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/characters')
def get_characters():
    """Return all characters from data.txt as JSON"""
    try:
        all_chars = load_characters()
        return jsonify({'characters': all_chars})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    new_chars = request.form['new_chars'].strip()
    start_char = request.form.get('start_char', '').strip()
    shuffle = 'shuffle' in request.form
    
    try:
        all_chars = load_characters()
        selected_chars = select_characters(new_chars, start_char, all_chars)
        
        if shuffle:
            random.shuffle(selected_chars)
        
        pdf_path = generate_pdf(selected_chars)
        
        return send_file(pdf_path, as_attachment=True, download_name='chinese_practice.pdf')
        
    except ValueError as e:
        # Return to form with error message
        return render_template('index.html', error=str(e), 
                             new_chars=new_chars, start_char=start_char, 
                             shuffle_checked='checked' if shuffle else '')

@app.route('/generate-custom', methods=['POST'])
def generate_custom():
    custom_text = request.form['custom_chars'].strip()
    shuffle = 'shuffle' in request.form
    
    try:
        # Filter and deduplicate Chinese characters
        filtered_chars = filter_chinese_characters(custom_text)
        
        if not filtered_chars:
            raise ValueError("No Chinese characters found in the pasted text")
        
        # Convert to list for shuffling if needed
        char_list = list(filtered_chars)
        
        if shuffle:
            random.shuffle(char_list)
        
        pdf_path = generate_pdf(char_list)
        
        # Generate filename with character count
        char_count = len(char_list)
        filename = f'chinese_custom_{char_count}chars.pdf'
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
        
    except ValueError as e:
        # Return to form with error message
        return render_template('index.html', error=str(e), 
                             custom_chars=custom_text,
                             custom_shuffle_checked='checked' if shuffle else '')

if __name__ == '__main__':
    # Use debug=False for production deployment
    app.run(debug=False, host='0.0.0.0', port=9527)
