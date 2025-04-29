import requests
import os
import json
import re
from typing import Tuple, Dict, Any
from producer_check import producer_check
from modify_check import modify_detect
from img_qr_reader import qrcode_data

def check_producer(file_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Check the producer of the PDF document
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (is_valid, result_data)
    """
    try:
        is_valid = producer_check(file_path)
        return is_valid, {
            'result': 'pass' if is_valid else 'fail',
            'producer': str(is_valid).lower()
        }
    except Exception as e:
        return False, {
            'result': 'error',
            'message': str(e)
        }

def check_modification(file_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if the PDF document has been modified
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (is_valid, result_data)
    """
    try:
        is_valid, modify_result = modify_detect(file_path)
        return is_valid, {
            'result': 'pass' if is_valid else 'fail',
            'modify': str(is_valid).lower(),
            'modify_result': modify_result
        }
    except Exception as e:
        return False, {
            'result': 'error',
            'message': str(e)
        }

def check_qrcode(file_path: str, output_img: str = 'test.png', api_url: str = "http://localhost:8000") -> Tuple[bool, Dict[str, Any]]:
    """
    Check QR codes in the PDF document and compare with extracted content
    
    Args:
        file_path (str): Path to the PDF file
        output_img (str): Path to save the QR code image
        api_url (str): Base URL for the API
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (is_valid, result_data)
    """
    try:
        # Get QR code data
        qr_data = qrcode_data(file_path, output_img)
        
        # Call API to convert PDF
        api_endpoint = f"{api_url}/convert-pdf-with-images"
        params = {
            "max_tokens": 2000,
            "temperature": 0.1,
            "system_prompt": "Summarize the content into json",
            "user_prompt": '''Summarize the content in English into json, must include {
                "Name": "",
                "Bank_code": "",
                "User_address": "",
                "Bank_address": "",
                "Account_Number": "",
                "Statement_Date": "",
                "Account_type": "",
                ...<other data>
            Make sure main details are totally correct.
            "User_address" do not add any extra details that not shown in file, do not use comma to separate address new line.
            only return json.''',
            "model": "gemma-3-27b-it-qat"
        }

        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(api_endpoint, params=params, files=files)

        if response.status_code != 200:
            return False, {
                'result': 'fail',
                'qrcode': 'false',
                'api_error': f'Failed to process PDF content (Status: {response.status_code})'
            }

        # Store the API response
        api_result = response.json()

        try:
            # Extract the nested JSON from the result
            json_str_match = re.search(r'```json\n(.*?)\n```', api_result.get('result', ''), re.DOTALL)

            if not json_str_match:
                # If no ```json ``` found, try to parse the entire result string if it looks like JSON
                json_str_match = re.search(r'({.*})', api_result.get('result', ''), re.DOTALL)

            if json_str_match:
                # Clean the JSON string
                json_content = json_str_match.group(1).strip()
                # Remove any potential trailing commas before closing brackets/braces
                json_content = re.sub(r',\s*}', '}', json_content)
                json_content = re.sub(r',\s*]', ']', json_content)

                pdf_data = json.loads(json_content)
                # Compare user address from PDF with QR code data
                pdf_address = pdf_data.get('User_address', '').strip().replace('\n', ' ').replace(',','') # Normalize address
                qr_address = qr_data.replace('Address: ', '').strip().replace('\n', ' ').replace(',','') # Normalize address

                # Simple comparison (consider more robust comparison if needed)
                if pdf_address == qr_address:
                    return True, {
                        'result': 'pass',
                        'qrcode': 'true',
                        'qrcode_data': qr_data,
                        'api_result': api_result
                    }
                else:
                    return False, {
                        'result': 'fail',
                        'qrcode': 'false',
                        'qr_result': {
                            'result': f'Address mismatch:\nPDF Address: `{pdf_address}`\nQR Code Address: `{qr_address}`'
                        }
                    }
            else:
                return False, {
                    'result': 'fail',
                    'qrcode': 'unknown',
                    'api_error': 'Failed to find or parse JSON in response'
                }
        except json.JSONDecodeError as e:
            return False, {
                'result': 'fail',
                'qrcode': 'unknown',
                'api_error': f'JSON parsing error: {str(e)}'
            }
        except Exception as e:
            return False, {
                'result': 'fail',
                'qrcode': 'unknown',
                'api_error': f'Error processing response: {str(e)}'
            }

    except Exception as e:
        return False, {
            'result': 'error',
            'message': str(e)
        }

def extract_content(file_path: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Extract content from the PDF document
    
    Args:
        file_path (str): Path to the PDF file
        api_url (str): Base URL for the API
        
    Returns:
        Dict[str, Any]: Extracted content (in JSON format)
    """
    try:
        api_endpoint = f"{api_url}/convert-pdf-with-images"
        params = {
            "max_tokens": 7500,
            "temperature": 0.1,
            "system_prompt": "Summarize the content into json",
            "user_prompt": '''Summarize the content in English into json, must include {
                "Name": "",
                "Bank_code": "",
                "User_address": "",
                "Bank_address": "",
                "Account_Number": "",
                "Statement_Date": "",
                "Account_type": "",
                ...<Other Suitable data into sub-json>
            }, if data do not provided use blank or null.
            only return json.'''
        }
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(api_endpoint, params=params, files=files)
            
        if response.status_code != 200:
            raise Exception("Failed to extract content from PDF")
            
        return response.json()
    except Exception as e:
        raise Exception(f"Error extracting content: {str(e)}")

def validate_document(file_path: str, api_url: str = "http://localhost:8000") -> Tuple[bool, Dict[str, Any]]:
    """
    Perform all validation steps
    
    Args:
        file_path (str): Path to the PDF file
        api_url (str): Base URL for the API
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (is_valid, result_data)
    """
    try:
        # Step 1: Producer check
        producer_valid, producer_result = check_producer(file_path)
        if not producer_valid:
            return False, {
                'result': 'fail',
                'producer': 'false',
                'modify': 'unknown',
                'qrcode': 'unknown'
            }

        # Step 2: Modification check
        modify_valid, modify_result = check_modification(file_path)
        if not modify_valid:
            return False, {
                'result': 'fail',
                'producer': 'true',
                'modify': 'false',
                'qrcode': 'unknown',
                'modify_result': modify_result.get('modify_result')
            }

        # Step 3: QR code check
        qrcode_valid, qrcode_result = check_qrcode(file_path, api_url=api_url)
        if not qrcode_valid:
            return False, {
                'result': 'fail',
                'producer': 'true',
                'modify': 'true',
                'qrcode': 'false',
                'qr_result': qrcode_result.get('qr_result')
            }

        # Extract content
        content = extract_content(file_path, api_url=api_url)

        # All checks passed
        return True, {
            'result': 'pass',
            'producer': 'true',
            'modify': 'true',
            'qrcode': 'true',
            'content': content
        }

    except Exception as e:
        return False, {
            'result': 'error',
            'message': str(e)
        } 