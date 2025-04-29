from estatement_validator import validate_document, check_producer, check_modification, check_qrcode, extract_content

def main():
    # Example PDF file path
    pdf_path = "/Users/chenziwen/Desktop/e-statement_test/template.pdf"
    api_url = "http://localhost:8000"
    
    # Method 1: Using individual validation functions
    print("=== Individual Validation ===")
    
    # Check producer
    producer_valid, producer_result = check_producer(pdf_path)
    print(f"Producer Check: {'Pass' if producer_valid else 'Fail'}")
    print(f"Result: {producer_result}\n")
    
    # Check modification
    modify_valid, modify_result = check_modification(pdf_path)
    print(f"Modification Check: {'Pass' if modify_valid else 'Fail'}")
    print(f"Result: {modify_result}\n")
    
    # Check QR code
    qrcode_valid, qrcode_result = check_qrcode(pdf_path, api_url=api_url)
    print(f"QR Code Check: {'Pass' if qrcode_valid else 'Fail'}")
    print(f"Result: {qrcode_result}\n")
    
    # Extract content
    try:
        content = extract_content(pdf_path, api_url=api_url)
        print("Extracted Content:")
        print(content)
    except Exception as e:
        print(f"Content extraction failed: {str(e)}")
    
    print("\n=== Complete Validation ===")
    # Method 2: Using complete validation function
    is_valid, result = validate_document(pdf_path, api_url=api_url)
    
    print(f"Document Validation: {'Pass' if is_valid else 'Fail'}")
    print("\nDetailed Results:")
    print(f"Producer Check: {result.get('producer', 'unknown')}")
    print(f"Modification Check: {result.get('modify', 'unknown')}")
    print(f"QR Code Check: {result.get('qrcode', 'unknown')}")
    
    if is_valid:
        print("\nExtracted Content:")
        print(result.get('content', {}))



if __name__ == "__main__":
    main()
    