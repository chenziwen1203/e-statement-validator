"""
E-Statement Validator Module

This module provides functionality to validate electronic statements (PDF documents)
by checking their producer, modifications, QR codes, and content.

Main Functions:
    - validate_document: Main function to validate a document
    - check_producer: Check PDF document producer
    - check_modification: Check if PDF has been modified
    - check_qrcode: Check QR codes in the document
    - extract_content: Extract content from the document
"""

from estatement_validator import (
    validate_document,
    check_producer,
    check_modification,
    check_qrcode,
    extract_content
)

__version__ = '1.0.0'
__all__ = [
    'validate_document',
    'check_producer',
    'check_modification',
    'check_qrcode',
    'extract_content'
] 