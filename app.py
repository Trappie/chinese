from flask import Flask, render_template, request, send_file, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import inch
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

def generate_smart_filename(new_chars, start_char, all_chars):
    """
    Generate filename in format: new_chars(下一个next_char).pdf
    """
    try:
        new_char_list = list(new_chars)
        num_new = len(new_char_list)
        num_old = 50 - num_new
        
        if num_old <= 0:
            # Only new characters, no review - use simple filename
            return f'{new_chars}.pdf'
        
        # Find the starting index
        start_index = all_chars.index(start_char)
        
        # Calculate how many review characters we collected
        # We go backward from start_index, collecting num_old characters
        # The last character we collect is at index: start_index - (num_old - 1)
        # So the next starting point is: start_index - num_old
        
        next_start_index = start_index - num_old
        
        # Handle wraparound case
        if next_start_index < 0:
            next_start_index = len(all_chars) + next_start_index
        
        next_start_char = all_chars[next_start_index]
        
        # Generate filename
        filename = f'{new_chars}(下一个{next_start_char}).pdf'
        return filename
        
    except Exception as e:
        # Fallback to simple filename if anything goes wrong
        return f'{new_chars}.pdf'

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

def generate_exponential_problem(difficulty):
    """
    Generate a single exponential math problem based on difficulty level
    Returns a tuple: (problem_text, answer_text)
    """
    # Set ranges based on difficulty
    if difficulty == 'easy':
        base_range = (2, 9)
        exp_range = (1, 5)
        allow_negative = False
    elif difficulty == 'medium':
        base_range = (2, 12)
        exp_range = (1, 10)
        allow_negative = True
    else:  # hard
        base_range = (2, 15)
        exp_range = (1, 15)
        allow_negative = True
    
    # Choose problem type
    problem_types = ['product', 'quotient', 'power']
    if allow_negative:
        problem_types.append('negative')
    
    problem_type = random.choice(problem_types)
    base = random.randint(*base_range)
    
    if problem_type == 'product':
        # a^m × a^n = a^(m+n)
        exp1 = random.randint(*exp_range)
        exp2 = random.randint(*exp_range)
        if allow_negative and random.random() < 0.3:
            exp1 = -exp1 if random.random() < 0.5 else exp1
            exp2 = -exp2 if random.random() < 0.5 else exp2
        
        problem = f"{base}^{{{exp1}}} × {base}^{{{exp2}}}"
        answer = f"{base}^{{{exp1 + exp2}}}"
        
    elif problem_type == 'quotient':
        # a^m ÷ a^n = a^(m-n)
        exp1 = random.randint(*exp_range)
        exp2 = random.randint(*exp_range)
        if allow_negative and random.random() < 0.3:
            exp1 = -exp1 if random.random() < 0.5 else exp1
            exp2 = -exp2 if random.random() < 0.5 else exp2
        
        problem = f"{base}^{{{exp1}}} ÷ {base}^{{{exp2}}}"
        answer = f"{base}^{{{exp1 - exp2}}}"
        
    elif problem_type == 'power':
        # (a^m)^n = a^(m×n)
        exp1 = random.randint(*exp_range)
        exp2 = random.randint(2, min(5, exp_range[1]))  # Keep multiplied result reasonable
        if allow_negative and random.random() < 0.3:
            exp1 = -exp1 if random.random() < 0.5 else exp1
            exp2 = -exp2 if random.random() < 0.5 else exp2
        
        problem = f"({base}^{{{exp1}}})^{{{exp2}}}"
        answer = f"{base}^{{{exp1 * exp2}}}"
        
    else:  # negative
        # a^(-n) = 1/a^n or mixed operations with negatives
        if random.random() < 0.5:
            # Simple negative exponent
            exp = random.randint(2, exp_range[1])
            problem = f"{base}^{{-{exp}}}"
            answer = f"1/{base}^{{{exp}}}"
        else:
            # Mixed operation with negative
            exp1 = random.randint(*exp_range)
            exp2 = -random.randint(1, exp_range[1])
            operation = random.choice(['×', '÷'])
            
            if operation == '×':
                problem = f"{base}^{{{exp1}}} × {base}^{{{exp2}}}"
                answer = f"{base}^{{{exp1 + exp2}}}"
            else:
                problem = f"{base}^{{{exp1}}} ÷ {base}^{{{exp2}}}"
                answer = f"{base}^{{{exp1 - exp2}}}"
    
    return problem, answer

def format_exponent_text(text):
    """
    Convert text with curly braces to superscript format for PDF
    Example: "2^{3}" becomes displayable superscript format
    """
    # This will be handled in the PDF generation
    return text

def generate_math_pdf(problems, num_problems):
    """
    Generate PDF with math problems in 2x3 grid (6 problems per page)
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    c = canvas.Canvas(temp_file.name, pagesize=letter)
    
    width, height = letter  # 612 x 792 points
    margin = 50
    
    # Grid layout: 2 columns × 3 rows = 6 problems per page
    cols_per_page = 2
    rows_per_page = 3
    problems_per_page = cols_per_page * rows_per_page
    
    # Calculate cell dimensions
    cell_width = (width - 2 * margin) / cols_per_page
    cell_height = (height - 2 * margin) / rows_per_page
    
    x_start = margin
    y_start = height - margin - cell_height
    
    for i, (problem, answer) in enumerate(problems):
        page_num = i // problems_per_page
        problem_on_page = i % problems_per_page
        row = problem_on_page // cols_per_page
        col = problem_on_page % cols_per_page
        
        # Check if we need a new page
        if i > 0 and problem_on_page == 0:
            c.showPage()
        
        x = x_start + col * cell_width
        y = y_start - row * cell_height
        
        # Draw cell border
        c.rect(x, y, cell_width, cell_height)
        
        # Draw problem number
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x + 10, y + cell_height - 20, f"Problem {i + 1}:")
        
        # Draw the math problem
        c.setFont("Helvetica", 14)
        
        # Split problem into base and exponent parts for better formatting
        problem_y = y + cell_height - 50
        
        # Simple approach: replace ^{} with ^ and handle basic superscripts
        display_problem = problem.replace('^{', '^').replace('}', '')
        
        # Draw problem
        c.drawString(x + 10, problem_y, display_problem + " = ?")
        
        # Add some space for student work
        c.setFont("Helvetica", 10)
        c.drawString(x + 10, y + 30, "Answer:")
        
        # Draw horizontal line for answer
        c.line(x + 60, y + 30, x + cell_width - 10, y + 30)
        
        # Optional: Add small answer in corner (can be removed for blank worksheets)
        c.setFont("Helvetica", 8)
        display_answer = answer.replace('^{', '^').replace('}', '')
        c.drawString(x + cell_width - 100, y + 10, f"({display_answer})")
    
    c.save()
    return temp_file.name

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

@app.route('/add-character', methods=['POST'])
def add_character():
    """Add a character to the end of data.txt"""
    try:
        char = request.json.get('character', '').strip()
        
        if not char:
            return jsonify({'error': 'No character provided'}), 400
        
        if len(char) != 1:
            return jsonify({'error': 'Only single characters are allowed'}), 400
        
        # Check if it's a valid Chinese character
        import re
        chinese_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]'
        if not re.match(chinese_pattern, char):
            return jsonify({'error': 'Only Chinese characters are allowed'}), 400
        
        # Load current characters
        all_chars = load_characters()
        
        # Check if character already exists
        if char in all_chars:
            return jsonify({'error': f'Character "{char}" already exists in database'}), 400
        
        # Append character to data.txt
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, 'data.txt')
        
        with open(data_path, 'a', encoding='utf-8') as f:
            f.write(char)
        
        # Get the new index
        new_index = len(all_chars)
        
        return jsonify({
            'success': True, 
            'message': f'Character "{char}" added to database at index {new_index}',
            'index': new_index
        })
        
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
        
        # Generate smart filename: new_chars(下一个next_char).pdf
        filename = generate_smart_filename(new_chars, start_char, all_chars)
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
        
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

@app.route('/generate-math', methods=['POST'])
def generate_math():
    problem_type = request.form.get('problem_type', 'exponential')
    difficulty = request.form.get('difficulty', 'medium')
    num_problems = int(request.form.get('num_problems', 6))
    
    try:
        # Generate problems
        problems = []
        for _ in range(num_problems):
            if problem_type == 'exponential':
                problem, answer = generate_exponential_problem(difficulty)
                problems.append((problem, answer))
        
        # Generate PDF
        pdf_path = generate_math_pdf(problems, num_problems)
        
        # Generate filename
        pages = (num_problems + 5) // 6  # Round up to nearest page
        filename = f'math_exponential_{difficulty}_{num_problems}problems_{pages}pages.pdf'
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        # Return to form with error message
        return render_template('index.html', error=f"Math generation error: {str(e)}")

if __name__ == '__main__':
    # Use debug=False for production deployment
    app.run(debug=False, host='0.0.0.0', port=9527)
