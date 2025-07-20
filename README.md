# Chinese Character Practice Generator

A web application that generates PDF practice sheets for learning Chinese characters.

## Features

- **Character Selection**: Choose new characters to learn and review starting point
- **Smart Logic**: Automatically selects 50 characters (new + review) with validation
- **PDF Generation**: Creates 5x10 grid practice sheets
- **Shuffle Option**: Randomly arrange characters (enabled by default)
- **Input Validation**: Ensures characters exist in database and follow learning rules

## Requirements

- New characters must have indices > 50 in the character database
- Review starting point must be < smallest new character index
- All characters must exist in data.txt
- Generates exactly 50 unique characters per PDF

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd chinese
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and go to `http://localhost:5000`

3. Enter:
   - **New Characters**: Characters your child is newly learning
   - **Starting Character**: Where to start selecting review characters
   - **Shuffle**: Check to randomize character order (default: on)

4. Click "Generate Practice PDF" to download the practice sheet

## Character Database

The `data.txt` file contains 500 unique Chinese characters covering:
- Numbers and basic characters (indices 0-50)
- Learning characters (indices 51+)
- Various categories: people, objects, colors, actions, feelings, etc.

## Testing

Run the unit tests to verify the character selection logic:

```bash
python test_character_selection.py
```

Tests cover:
- Normal usage scenarios
- Input validation and error handling
- Edge cases (wraparound, boundary conditions)
- Real data verification

## Project Structure

```
chinese/
├── app.py                    # Main Flask application
├── data.txt                  # 500 unique Chinese characters
├── requirements.txt          # Python dependencies
├── test_character_selection.py  # Unit tests
├── templates/
│   └── index.html           # Web interface
└── static/                  # Future CSS/JS files
```

## API

The application validates:
1. All new characters exist in data.txt
2. All new characters have indices > 50
3. Review starting character exists in data.txt
4. Review starting character index < min(new character indices)

Returns appropriate error messages for invalid inputs.

## License

This project is for educational purposes.