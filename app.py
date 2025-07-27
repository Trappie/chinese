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
        problem_types = ['product', 'quotient', 'power']
    elif difficulty == 'medium':
        base_range = (2, 12)
        exp_range = (1, 10)
        allow_negative = True
        problem_types = ['product', 'quotient', 'power', 'negative']
    else:  # hard
        base_range = (2, 8)  # Smaller bases for complex problems
        exp_range = (1, 8)   # Smaller exponents for readability
        allow_negative = True
        problem_types = ['product', 'quotient', 'power', 'negative', 'multi_part', 'fraction_mix']
    
    problem_type = random.choice(problem_types)
    
    if problem_type == 'multi_part' and difficulty == 'hard':
        # Generate complex 3+ part problems for hard difficulty
        return generate_multi_part_problem(base_range, exp_range)
    elif problem_type == 'fraction_mix' and difficulty == 'hard':
        # Generate fraction notation mixed with negative exponents
        return generate_fraction_mix_problem(base_range, exp_range)
    else:
        # Standard 2-part problems (works for all difficulties)
        return generate_standard_problem(problem_type, base_range, exp_range, allow_negative)

def generate_multi_part_problem(base_range, exp_range):
    """
    Generate complex multi-part problems like: a^m × (a^n)^p ÷ a^q
    """
    base = random.randint(*base_range)
    num_parts = random.choice([3, 4])  # 3 or 4 parts
    
    # Generate different operation combinations
    patterns = [
        # 3-part patterns
        ['product', 'power', 'quotient'],    # a^m × (a^n)^p ÷ a^q
        ['power', 'product', 'quotient'],    # (a^m)^n × a^p ÷ a^q
        ['quotient', 'power', 'product'],    # a^m ÷ (a^n)^p × a^q
        # 4-part patterns
        ['product', 'quotient', 'power', 'product'],  # a^m × a^n ÷ (a^p)^q × a^r
        ['power', 'product', 'quotient', 'power'],    # (a^m)^n × a^p ÷ (a^q)^r
    ]
    
    pattern = random.choice(patterns[:3] if num_parts == 3 else patterns[3:])
    
    # Generate exponents
    exponents = [random.randint(*exp_range) for _ in range(num_parts)]
    
    # Add some negative exponents
    for i in range(len(exponents)):
        if random.random() < 0.3:
            exponents[i] = -exponents[i]
    
    # Build problem string and calculate answer
    parts = []
    operations = []
    running_exponent = 0
    
    for i, (op, exp) in enumerate(zip(pattern, exponents)):
        if op == 'power':
            if i == 0:
                power_exp = random.randint(2, 4)
                parts.append(f"({base}^{{{exp}}})^{{{power_exp}}}")
                running_exponent += exp * power_exp
            else:
                power_exp = random.randint(2, 3)
                parts.append(f"({base}^{{{exp}}})^{{{power_exp}}}")
                if operations[-1] == '×':
                    running_exponent += exp * power_exp
                elif operations[-1] == '÷':
                    running_exponent -= exp * power_exp
        else:
            parts.append(f"{base}^{{{exp}}}")
            if i == 0:
                running_exponent = exp
            else:
                if operations[-1] == '×':
                    running_exponent += exp
                elif operations[-1] == '÷':
                    running_exponent -= exp
        
        # Add operation for next part
        if i < len(pattern) - 1:
            if pattern[i+1] == 'product' or (i == 0 and pattern[i+1] != 'quotient'):
                operations.append('×')
            else:
                operations.append('÷')
    
    # Construct the problem string
    problem = parts[0]
    for i, op in enumerate(operations):
        problem += f" {op} {parts[i+1]}"
    
    answer = f"{base}^{{{running_exponent}}}"
    return problem, answer

def generate_fraction_mix_problem(base_range, exp_range):
    """
    Generate problems mixing fractions and negative exponents like: (1/a)^n × a^(-m)
    """
    base = random.randint(*base_range)
    
    # Different fraction mix patterns
    patterns = [
        'fraction_times_negative',    # (1/a)^n × a^(-m)
        'fraction_times_positive',    # (1/a)^n × a^m
        'fraction_divide_negative',   # (1/a)^n ÷ a^(-m)
        'power_of_fraction',          # ((1/a)^n)^m
        'complex_fraction_mix'        # (1/a)^n × a^m ÷ a^(-p)
    ]
    
    pattern = random.choice(patterns)
    
    if pattern == 'fraction_times_negative':
        # (1/a)^n × a^(-m) = a^(-n) × a^(-m) = a^(-n-m)
        exp1 = random.randint(1, exp_range[1])
        exp2 = random.randint(1, exp_range[1])
        problem = f"(1/{base})^{{{exp1}}} × {base}^{{-{exp2}}}"
        answer = f"{base}^{{-{exp1 + exp2}}}"
        
    elif pattern == 'fraction_times_positive':
        # (1/a)^n × a^m = a^(-n) × a^m = a^(m-n)
        exp1 = random.randint(1, exp_range[1])
        exp2 = random.randint(1, exp_range[1])
        problem = f"(1/{base})^{{{exp1}}} × {base}^{{{exp2}}}"
        result_exp = exp2 - exp1
        answer = f"{base}^{{{result_exp}}}"
        
    elif pattern == 'fraction_divide_negative':
        # (1/a)^n ÷ a^(-m) = a^(-n) ÷ a^(-m) = a^(-n+m) = a^(m-n)
        exp1 = random.randint(1, exp_range[1])
        exp2 = random.randint(1, exp_range[1])
        problem = f"(1/{base})^{{{exp1}}} ÷ {base}^{{-{exp2}}}"
        result_exp = exp2 - exp1
        answer = f"{base}^{{{result_exp}}}"
        
    elif pattern == 'power_of_fraction':
        # ((1/a)^n)^m = (a^(-n))^m = a^(-n×m)
        exp1 = random.randint(1, exp_range[1])
        exp2 = random.randint(2, 4)
        problem = f"((1/{base})^{{{exp1}}})^{{{exp2}}}"
        answer = f"{base}^{{-{exp1 * exp2}}}"
        
    else:  # complex_fraction_mix
        # (1/a)^n × a^m ÷ a^(-p) = a^(-n) × a^m ÷ a^(-p) = a^(-n+m+p)
        exp1 = random.randint(1, exp_range[1])
        exp2 = random.randint(1, exp_range[1])
        exp3 = random.randint(1, exp_range[1])
        problem = f"(1/{base})^{{{exp1}}} × {base}^{{{exp2}}} ÷ {base}^{{-{exp3}}}"
        result_exp = -exp1 + exp2 + exp3
        answer = f"{base}^{{{result_exp}}}"
    
    return problem, answer

def generate_standard_problem(problem_type, base_range, exp_range, allow_negative):
    """
    Generate standard 2-part exponential problems
    """
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
        exp2 = random.randint(2, min(5, exp_range[1]))
        if allow_negative and random.random() < 0.3:
            exp1 = -exp1 if random.random() < 0.5 else exp1
            exp2 = -exp2 if random.random() < 0.5 else exp2
        
        problem = f"({base}^{{{exp1}}})^{{{exp2}}}"
        answer = f"{base}^{{{exp1 * exp2}}}"
        
    else:  # negative
        # a^(-n) = 1/a^n or mixed operations with negatives
        if random.random() < 0.5:
            exp = random.randint(2, exp_range[1])
            problem = f"{base}^{{-{exp}}}"
            answer = f"1/{base}^{{{exp}}}"
        else:
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

def draw_math_expression(canvas, x, y, expression, font_size=14):
    """
    Draw a mathematical expression with proper formatting for exponents and fractions
    Returns the width of the drawn expression
    """
    import re
    
    # Parse the expression for different components
    parts = []
    current_x = x
    
    # Split expression into tokens (base, exponent, operators, etc.)
    # Handle patterns like: base^{exponent}, (base^{exponent}), fractions
    
    # First, handle parentheses groups
    expression = expression.replace('(', '( ').replace(')', ' )')
    tokens = expression.split()
    
    for token in tokens:
        if token == '(':
            canvas.setFont("Helvetica", font_size)
            canvas.drawString(current_x, y, '(')
            current_x += canvas.stringWidth('(', "Helvetica", font_size)
            
        elif token == ')':
            canvas.setFont("Helvetica", font_size)
            canvas.drawString(current_x, y, ')')
            current_x += canvas.stringWidth(')', "Helvetica", font_size)
            
        elif token in ['×', '÷', '=']:
            # Draw operators with some spacing
            canvas.setFont("Helvetica", font_size)
            current_x += 5  # Add space before operator
            canvas.drawString(current_x, y, token)
            current_x += canvas.stringWidth(token, "Helvetica", font_size) + 5
            
        elif '^{' in token:
            # Handle base^{exponent}
            base, exp_part = token.split('^{', 1)
            exponent = exp_part.rstrip('}')
            
            # Draw base
            canvas.setFont("Helvetica", font_size)
            canvas.drawString(current_x, y, base)
            current_x += canvas.stringWidth(base, "Helvetica", font_size)
            
            # Draw exponent (smaller and higher)
            exp_font_size = int(font_size * 0.7)
            exp_y = y + font_size * 0.3
            canvas.setFont("Helvetica", exp_font_size)
            canvas.drawString(current_x, exp_y, exponent)
            current_x += canvas.stringWidth(exponent, "Helvetica", exp_font_size)
            
        elif token.startswith('(1/') and ')^{' in token:
            # Handle fraction notation like (1/base)^{exponent}
            # Extract base and exponent
            inner = token[3:]  # Remove "(1/"
            base_part, exp_part = inner.split(')^{', 1)
            exponent = exp_part.rstrip('}')
            
            # Draw opening parenthesis
            canvas.setFont("Helvetica", font_size)
            canvas.drawString(current_x, y, '(')
            current_x += canvas.stringWidth('(', "Helvetica", font_size)
            
            # Draw "1" numerator
            canvas.drawString(current_x, y + font_size * 0.3, '1')
            num_width = canvas.stringWidth('1', "Helvetica", font_size)
            
            # Draw base of denominator
            canvas.drawString(current_x, y - font_size * 0.2, base_part)
            base_width = canvas.stringWidth(base_part, "Helvetica", font_size)
            
            total_width = max(num_width, base_width)
            
            # Draw fraction line
            canvas.line(current_x, y, current_x + total_width, y)
            current_x += total_width
            
            # Draw closing parenthesis
            canvas.drawString(current_x, y, ')')
            current_x += canvas.stringWidth(')', "Helvetica", font_size)
            
            # Draw exponent (smaller and higher)
            exp_font_size = int(font_size * 0.7)
            exp_y = y + font_size * 0.3
            canvas.setFont("Helvetica", exp_font_size)
            canvas.drawString(current_x, exp_y, exponent)
            current_x += canvas.stringWidth(exponent, "Helvetica", exp_font_size)
            
        elif token.startswith('1/') and '^{' in token:
            # Handle fractions like 1/base^{exponent}
            # Draw "1" numerator
            canvas.setFont("Helvetica", font_size)
            canvas.drawString(current_x, y + font_size * 0.3, '1')
            num_width = canvas.stringWidth('1', "Helvetica", font_size)
            
            # Extract denominator
            denominator = token[2:]  # Remove "1/"
            if '^{' in denominator:
                base, exp_part = denominator.split('^{', 1)
                exponent = exp_part.rstrip('}')
                
                # Draw base of denominator
                canvas.setFont("Helvetica", font_size)
                canvas.drawString(current_x, y - font_size * 0.2, base)
                base_width = canvas.stringWidth(base, "Helvetica", font_size)
                
                # Draw exponent of denominator
                exp_font_size = int(font_size * 0.7)
                exp_y = y - font_size * 0.2 + font_size * 0.3
                canvas.setFont("Helvetica", exp_font_size)
                canvas.drawString(current_x + base_width, exp_y, exponent)
                exp_width = canvas.stringWidth(exponent, "Helvetica", exp_font_size)
                
                total_width = max(num_width, base_width + exp_width)
                
                # Draw fraction line
                canvas.line(current_x, y, current_x + total_width, y)
                current_x += total_width + 5
            else:
                # Simple fraction without exponent
                canvas.drawString(current_x, y - font_size * 0.2, denominator)
                denom_width = canvas.stringWidth(denominator, "Helvetica", font_size)
                total_width = max(num_width, denom_width)
                
                # Draw fraction line
                canvas.line(current_x, y, current_x + total_width, y)
                current_x += total_width + 5
        else:
            # Regular text
            canvas.setFont("Helvetica", font_size)
            canvas.drawString(current_x, y, token)
            current_x += canvas.stringWidth(token, "Helvetica", font_size)
    
    return current_x - x

def format_math_problem_for_display(problem_text):
    """
    Format math problem text for better display
    """
    # Add spaces around operators for better readability
    problem_text = problem_text.replace('×', ' × ').replace('÷', ' ÷ ')
    # Clean up multiple spaces
    problem_text = ' '.join(problem_text.split())
    return problem_text

def draw_question_page(canvas, problems_subset, page_number):
    """
    Draw a single question page with 6 problems in 2x3 grid
    """
    width, height = letter
    margin = 50
    
    # Grid layout: 2 columns × 3 rows = 6 problems per page
    cols_per_page = 2
    rows_per_page = 3
    
    # Calculate cell dimensions
    cell_width = (width - 2 * margin) / cols_per_page
    cell_height = (height - 2 * margin) / rows_per_page
    
    x_start = margin
    y_start = height - margin - cell_height
    
    # Add page header
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(margin, height - 30, f"Math Practice - Exponential Rules (Page {page_number})")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(margin, height - 45, "Name: ________________    Date: ________________")
    
    for i, (problem, answer) in enumerate(problems_subset):
        if i >= 6:  # Only 6 problems per page
            break
            
        row = i // cols_per_page
        col = i % cols_per_page
        
        x = x_start + col * cell_width
        y = y_start - row * cell_height
        
        # Draw cell border
        canvas.rect(x, y, cell_width, cell_height)
        
        # Draw problem number
        canvas.setFont("Helvetica-Bold", 12)
        problem_num = (page_number - 1) * 6 + i + 1
        canvas.drawString(x + 10, y + cell_height - 20, f"Problem {problem_num}:")
        
        # Draw the math problem with proper formatting
        problem_y = y + cell_height - 60
        
        # Format and draw the problem
        formatted_problem = format_math_problem_for_display(problem)
        problem_width = draw_math_expression(canvas, x + 10, problem_y, formatted_problem, 16)
        
        # Draw equals sign and question mark
        canvas.setFont("Helvetica", 16)
        canvas.drawString(x + 15 + problem_width, problem_y, " = ?")
        
        # Add clean answer area (just a box, no "Answer:" label)
        answer_box_x = x + 20
        answer_box_y = y + 20
        answer_box_width = cell_width - 40
        answer_box_height = 25
        canvas.rect(answer_box_x, answer_box_y, answer_box_width, answer_box_height)

def draw_answer_page(canvas, problems_subset, page_number):
    """
    Draw a single answer page with 6 answers in 2x3 grid
    """
    width, height = letter
    margin = 50
    
    # Grid layout: 2 columns × 3 rows = 6 problems per page
    cols_per_page = 2
    rows_per_page = 3
    
    # Calculate cell dimensions
    cell_width = (width - 2 * margin) / cols_per_page
    cell_height = (height - 2 * margin) / rows_per_page
    
    x_start = margin
    y_start = height - margin - cell_height
    
    # Add page header
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(margin, height - 30, f"Answer Key - Exponential Rules (Page {page_number})")
    
    for i, (problem, answer) in enumerate(problems_subset):
        if i >= 6:  # Only 6 problems per page
            break
            
        row = i // cols_per_page
        col = i % cols_per_page
        
        x = x_start + col * cell_width
        y = y_start - row * cell_height
        
        # Draw cell border
        canvas.rect(x, y, cell_width, cell_height)
        
        # Draw problem number
        canvas.setFont("Helvetica-Bold", 12)
        problem_num = (page_number - 1) * 6 + i + 1
        canvas.drawString(x + 10, y + cell_height - 20, f"Problem {problem_num}:")
        
        # Draw the complete equation with answer
        equation_y = y + cell_height - 60
        
        # Format and draw the problem
        formatted_problem = format_math_problem_for_display(problem)
        problem_width = draw_math_expression(canvas, x + 10, equation_y, formatted_problem, 14)
        
        # Draw equals sign
        canvas.setFont("Helvetica", 14)
        canvas.drawString(x + 15 + problem_width, equation_y, " = ")
        equals_width = canvas.stringWidth(" = ", "Helvetica", 14)
        
        # Draw the answer
        formatted_answer = format_math_problem_for_display(answer)
        draw_math_expression(canvas, x + 20 + problem_width + equals_width, equation_y, formatted_answer, 14)

def generate_math_pdf(problems, num_problems):
    """
    Generate PDF with math problems - questions and answers on separate pages for double-sided printing
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    c = canvas.Canvas(temp_file.name, pagesize=letter)
    
    # Calculate number of question pages needed (6 problems per page)
    problems_per_page = 6
    num_question_pages = (num_problems + problems_per_page - 1) // problems_per_page
    
    # Generate question pages
    for page_num in range(1, num_question_pages + 1):
        start_idx = (page_num - 1) * problems_per_page
        end_idx = min(start_idx + problems_per_page, num_problems)
        problems_subset = problems[start_idx:end_idx]
        
        if page_num > 1:
            c.showPage()
        
        draw_question_page(c, problems_subset, page_num)
    
    # Generate answer pages
    for page_num in range(1, num_question_pages + 1):
        start_idx = (page_num - 1) * problems_per_page
        end_idx = min(start_idx + problems_per_page, num_problems)
        problems_subset = problems[start_idx:end_idx]
        
        c.showPage()  # New page for answers
        draw_answer_page(c, problems_subset, page_num)
    
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
