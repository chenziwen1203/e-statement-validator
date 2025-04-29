import streamlit as st
import requests
import os
import tempfile
from typing import Tuple, Dict, Any
from producer_check import producer_check
from QRcode_check import verify_qr_info
from modify_check import modify_detect
from img_qr_reader import qrcode_data
import base64 # Import base64 for PDF display

# Configure page settings
st.set_page_config(
    page_title="PDF Verification System",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .result-card {
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .pass {
        background-color: #e6f7ee;
        border-left: 5px solid #28a745;
    }
    .fail {
        background-color: #fde8e8;
        border-left: 5px solid #dc3545;
    }
    .status-badge {
        font-size: 0.9rem;
        padding: 0.35em 0.65em;
    }
    /* Ensure iframe for PDF display fits well */
    iframe {
        width: 100%;
        min-height: 600px; /* Adjust height as needed */
        border: 1px solid #ddd; /* Optional border */
    }
    </style>
""", unsafe_allow_html=True)


def save_uploaded_file(uploaded_file):
    """Save uploaded file to temporary location"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        return tmp_file.name

# --- Function to display PDF ---
def show_pdf(file):
    """Displays the PDF file in the Streamlit app."""
    # Read file as bytes
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    # Embed PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" type="application/pdf"></iframe>'
    # Display HTML
    st.markdown(pdf_display, unsafe_allow_html=True)
# --- End of function ---


def verify_pdf(file_path: str) -> Tuple[bool, Dict[str, Any]]:
    """Execute the three verification steps"""
    try:
        # Step 1: Producer check
        producer_valid = producer_check(file_path)
        if not producer_valid:
            return False, {
                'result': 'fail',
                'producer': 'false',
                'modify': 'unknown',
                'qrcode': 'unknown'
            }

        # Step 2: Modification check
        modify_valid,modify_result = modify_detect(file_path)
        if not modify_valid:
            return False, {
                'result': 'fail',
                'producer': 'true',
                'modify': 'false',
                'qrcode': 'unknown',
                'modify_result':modify_result
            }

        # Step 3: QR Code check
        output_img='test.png'
        qr_data=qrcode_data(file_path,output_img)

        # Make API call to convert PDF
        api_url = "http://localhost:8000/convert-pdf-with-images"
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
            # gemma-3-4b-it
        }
        # ...<Other Suitable data into sub-json>

        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(api_url, params=params, files=files)

        if response.status_code != 200:
            return False, {
                'result': 'fail',
                'producer': 'true',
                'modify': 'true',
                'qrcode': 'unknown',
                'api_error': f'Failed to process PDF content (Status: {response.status_code})'
            }

        # Store the API response
        api_result = response.json()

        try:
            # Extract the nested JSON from the result
            import json
            import re

            # First try to find JSON in the result
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
                pdf_address = pdf_data.get('User_address', '').strip().replace('\n', ' ') # Normalize address
                qr_address = qr_data.replace('Address: ', '').strip().replace('\n', ' ') # Normalize address

                # Simple comparison (consider more robust comparison if needed)
                if pdf_address == qr_address:
                    # All checks passed
                    return True, {
                        'result': 'pass',
                        'producer': 'true',
                        'modify': 'true',
                        'qrcode': 'true',
                        'api_result': api_result
                    }
                else:
                    return False, {
                        'result': 'fail',
                        'producer': 'true',
                        'modify': 'true',
                        'qrcode': 'false',
                        'qr_result': {
                            'result': f'Address mismatch:\nPDF Address: `{pdf_address}`\nQR Code Address: `{qr_address}`'
                        }
                    }
            else:
                st.warning("Could not find JSON block in API response.") # Add warning
                st.json(api_result) # Show the raw API result for debugging
                return False, {
                    'result': 'fail',
                    'producer': 'true',
                    'modify': 'true',
                    'qrcode': 'unknown',
                    'api_error': 'Failed to find or parse JSON in response'
                }
        except json.JSONDecodeError as e:
            st.error(f"JSON Parsing Error: {e}") # Add error details
            st.text("Problematic JSON content:")
            st.code(json_content if 'json_content' in locals() else api_result.get('result','N/A'), language='json')
            return False, {
                'result': 'fail',
                'producer': 'true',
                'modify': 'true',
                'qrcode': 'unknown',
                'api_error': f'JSON parsing error: {str(e)}'
            }
        except Exception as e:
            st.error(f"Error processing API response: {e}") # Add error details
            return False, {
                'result': 'fail',
                'producer': 'true',
                'modify': 'true',
                'qrcode': 'unknown',
                'api_error': f'Error processing response: {str(e)}'
            }

    except Exception as e:
        st.error(f"Verification error: {str(e)}")
        # Log the full traceback for debugging if needed
        # import traceback
        # st.text(traceback.format_exc())
        return False, {
            'result': 'error',
            'message': str(e)
        }


def display_results(result_data: Dict[str, Any]):
    """Display verification results with visual indicators"""
    with st.container():
        # Main result card
        result_class = "pass" if result_data['result'] == 'pass' else "fail"
        result_text = result_data['result'].upper() if result_data['result'] != 'error' else 'ERROR'
        st.markdown(
            f"<div class='result-card {result_class}'>"
            f"<h3>Verification Result: <strong>{result_text}</strong></h3>"
            "</div>",
            unsafe_allow_html=True
        )

        if result_data['result'] == 'error':
            st.error(f"An error occurred during verification: {result_data.get('message', 'Unknown error')}")
            return # Stop further display if there was a critical error

        # Detailed results
        cols = st.columns(3)
        with cols[0]:
            status = result_data.get('producer', 'unknown')
            bg_class = 'success' if status == 'true' else 'danger' if status == 'false' else 'secondary'
            icon = '✓' if status == 'true' else '✗' if status == 'false' else '?'
            st.markdown(
                f"<div class='result-card'>"
                f"<h4>Producer Validation</h4>"
                f"<span class='status-badge badge bg-{bg_class}'>"
                f"{icon} {status}"
                f"</span>"
                "</div>",
                unsafe_allow_html=True
            )

        with cols[1]:
            status = result_data.get('modify', 'unknown')
            bg_class = 'success' if status == 'true' else 'danger' if status == 'false' else 'secondary'
            icon = '✓' if status == 'true' else '✗' if status == 'false' else '?'
            st.markdown(
                f"<div class='result-card'>"
                f"<h4>Content Modification</h4>"
                f"<span class='status-badge badge bg-{bg_class}'>"
                f"{icon} {status}"
                f"</span>"
                "</div>",
                unsafe_allow_html=True
            )

            # Display modify_result if available
            if 'modify_result' in result_data and result_data['modify_result']:
                st.markdown("**Modification Details:**")
                for detail in result_data['modify_result']:
                    st.markdown(f"- {detail}")

        with cols[2]:
            status = result_data.get('qrcode', 'unknown')
            bg_class = 'success' if status == 'true' else 'danger' if status == 'false' else 'secondary'
            icon = '✓' if status == 'true' else '✗' if status == 'false' else '?'
            st.markdown(
                f"<div class='result-card'>"
                f"<h4>QR Code Validation</h4>"
                f"<span class='status-badge badge bg-{bg_class}'>"
                f"{icon} {status}"
                f"</span>"
                "</div>",
                unsafe_allow_html=True
            )

        # Display QR code response if validation failed specifically on QR code check
        if result_data['result'] == 'fail' and result_data.get('qrcode') == 'false' and 'qr_result' in result_data:
            st.markdown("### QR Code Validation Details")
            st.warning(result_data['qr_result']['result']) # Use warning box for mismatch

        # Display API error if it occurred during QR code check or later
        if 'api_error' in result_data:
             st.error(f"API Processing Error: {result_data['api_error']}")

        # Display API result (extracted document info) if verification passed
        if result_data['result'] == 'pass' and 'api_result' in result_data:
            st.markdown("### Document Information (Extracted via API)")
            # Try to display the nested JSON result nicely
            try:
                import json
                import re
                # Reuse the extraction logic if possible
                api_response_text = result_data['api_result'].get('result', '')
                json_str_match = re.search(r'```json\n(.*?)\n```', api_response_text, re.DOTALL)
                if not json_str_match:
                    json_str_match = re.search(r'({.*})', api_response_text, re.DOTALL)

                if json_str_match:
                    json_content = json_str_match.group(1).strip()
                    json_content = re.sub(r',\s*}', '}', json_content)
                    json_content = re.sub(r',\s*]', ']', json_content)
                    parsed_json = json.loads(json_content)
                    st.json(parsed_json)
                else:
                    st.text("Could not extract JSON, showing raw API result:")
                    st.text(api_response_text) # Show raw text if parsing failed
            except Exception as e:
                 st.text("Error displaying extracted JSON, showing raw API result:")
                 st.text(result_data['api_result'].get('result', 'N/A'))


# Main App
st.title("🔍 PDF Verification System")
st.markdown("""
    Upload a PDF document to verify its authenticity through three security checks:
    1. **Producer Validation** - Checks document origin
    2. **Content Modification** - Detects unauthorized changes
    3. **QR Code Validation** - Verifies embedded security code against extracted text
""")

uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])

if uploaded_file is not None:
    # --- Display the uploaded PDF ---
    # Use an expander to make it optional to view
    with st.expander("View Uploaded PDF"):
        show_pdf(uploaded_file)
    # --- End PDF display ---

    if st.button("Verify Document", type="primary"):
        with st.spinner("Verifying document... Please wait."):
            # Save to temp file
            # Important: Need to reset the file pointer after reading it for display
            uploaded_file.seek(0)
            temp_path = save_uploaded_file(uploaded_file)

            # Perform verification
            is_valid, result_data = verify_pdf(temp_path)

            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception as e:
                st.warning(f"Could not delete temporary file: {temp_path}. Error: {e}")


            # Display results
            display_results(result_data)

            # Handle successful verification
            if is_valid:
                st.success("✅ All checks passed! Document appears authentic.")

            elif result_data['result'] != 'error': # If it failed but wasn't a critical error
                st.error("❌ Verification failed. Document may have been tampered with or information mismatch detected.")