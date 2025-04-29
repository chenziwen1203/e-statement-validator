# E-Statement Validator for Bank of China

A Python module specifically designed for validating Bank of China (BOC) electronic statements (PDF documents) by checking their authenticity, integrity, and content.

## Features

- **Producer Validation**: Verifies the PDF document's producer to ensure it's from Bank of China
- **Modification Detection**: Checks if the document has been modified after issuance
- **QR Code Verification**: Validates QR codes embedded in the document against extracted content
- **Content Extraction**: Extracts and structures document content in a standardized format
- **Comprehensive Validation**: Combines all checks into a single validation process

## Installation

```bash
pip install e-statement-validator
```

## Usage

### Basic Usage

```python
from estatement_validator import validate_document

# Validate a Bank of China e-statement
is_valid, result = validate_document("path/to/your/boc_statement.pdf")

if is_valid:
    print("Document is valid!")
    print("Extracted content:", result['content'])
else:
    print("Document validation failed:", result['message'])
```

### Individual Checks

You can also perform individual checks:

```python
from estatement_validator import (
    check_producer,
    check_modification,
    check_qrcode,
    extract_content
)

# Check producer (should be Bank of China)
is_valid, result = check_producer("boc_statement.pdf")

# Check for modifications
is_valid, result = check_modification("boc_statement.pdf")

# Check QR codes
is_valid, result = check_qrcode("boc_statement.pdf")

# Extract content
content = extract_content("boc_statement.pdf")
```

## API Reference

### validate_document(file_path: str, api_url: str = "http://localhost:8000") -> Tuple[bool, Dict[str, Any]]

Main function that performs all validation steps for Bank of China e-statements.

**Parameters:**
- `file_path`: Path to the BOC e-statement PDF file
- `api_url`: Base URL for the API (default: "http://localhost:8000")

**Returns:**
- Tuple containing:
  - Boolean indicating if document is valid
  - Dictionary with validation results and extracted content

### check_producer(file_path: str) -> Tuple[bool, Dict[str, Any]]

Checks if the PDF document was produced by Bank of China.

### check_modification(file_path: str) -> Tuple[bool, Dict[str, Any]]

Checks if the Bank of China e-statement has been modified.

### check_qrcode(file_path: str, output_img: str = 'test.png', api_url: str = "http://localhost:8000") -> Tuple[bool, Dict[str, Any]]

Validates QR codes in the BOC e-statement and compares with extracted content.

### extract_content(file_path: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]]

Extracts and structures the BOC e-statement content.

## Dependencies

- requests
- PyPDF2
- Pillow
- qrcode
- opencv-python

## Requirements

- Python 3.6+
- Bank of China e-statement in PDF format

## License

MIT License

## Contributing

[Contribution guidelines will be added here] 