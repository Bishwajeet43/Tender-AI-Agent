"""Tender AI Agent - Main Flask Application

This Flask application automates NIT PDF processing for M/S JEETTECNIKA.
It handles PDF uploads, extracts item details, and generates emails for BQ requests
and OEM authorization workflows.
"""

from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import PyPDF2
import re
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Company details for M/S JEETTECNIKA
COMPANY_DETAILS = {
    'name': 'M/S JEETTECNIKA',
    'address': '',  # Add company address
    'email': '',    # Add company email
    'phone': '',    # Add company phone
    'website': ''   # Add company website
}

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


def allowed_file(filename):
    """Check if uploaded file has an allowed extension.
    
    Args:
        filename (str): Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from all pages of the PDF
    """
    text = ''
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
    return text


def parse_nit_items(text):
    """Parse NIT PDF text to extract item details.
    
    This function extracts structured information about items from the NIT document,
    including item numbers, descriptions, quantities, and specifications.
    
    Args:
        text (str): Extracted text from NIT PDF
        
    Returns:
        list: List of dictionaries containing item details
    """
    items = []
    
    # TODO: Implement parsing logic based on NIT PDF structure
    # This is a placeholder implementation
    # Customize based on actual NIT PDF format
    
    # Example structure - modify according to actual NIT format
    lines = text.split('\n')
    
    for line in lines:
        # Pattern matching for item entries (customize as needed)
        # Example: Looking for lines with item numbers and descriptions
        if re.match(r'^\d+\.', line.strip()):
            item = {
                'item_no': '',
                'description': '',
                'quantity': '',
                'unit': '',
                'specifications': ''
            }
            # Extract item details (implement actual parsing logic)
            items.append(item)
    
    return items


def generate_bq_request_email(items, tender_details):
    """Generate email text for Bill of Quantities (BQ) request.
    
    Args:
        items (list): List of extracted items from NIT
        tender_details (dict): Details about the tender
        
    Returns:
        str: Formatted email text for BQ request
    """
    email_template = f"""
Subject: Request for Bill of Quantities - {tender_details.get('tender_name', 'NIT')}

Dear Sir/Madam,

We, {COMPANY_DETAILS['name']}, are writing to request the Bill of Quantities (BQ) for the following tender:

Tender Reference: {tender_details.get('tender_ref', 'N/A')}
Tender Name: {tender_details.get('tender_name', 'N/A')}
Issue Date: {tender_details.get('issue_date', 'N/A')}

We would appreciate receiving the detailed Bill of Quantities for the items listed in the Notice Inviting Tender.

Total Items: {len(items)}

Please provide the BQ at your earliest convenience to enable us to prepare our quotation.

Thank you for your cooperation.

Best regards,
{COMPANY_DETAILS['name']}
{COMPANY_DETAILS.get('email', '')}
{COMPANY_DETAILS.get('phone', '')}
    """
    
    return email_template


def generate_oem_authorization_email(items, oem_name):
    """Generate email text for OEM authorization request.
    
    Args:
        items (list): List of items requiring OEM authorization
        oem_name (str): Name of the OEM manufacturer
        
    Returns:
        str: Formatted email text for OEM authorization request
    """
    current_date = datetime.now().strftime('%B %d, %Y')
    
    email_template = f"""
Subject: Request for OEM Authorization Certificate - {oem_name}

Dear {oem_name} Team,

We, {COMPANY_DETAILS['name']}, are an authorized dealer/distributor interested in participating in government tenders.

We kindly request an OEM Authorization Certificate for the following items/products:

"""
    
    # Add item details to email
    for idx, item in enumerate(items, 1):
        email_template += f"{idx}. {item.get('description', 'N/A')}\n"
    
    email_template += f"""

The authorization certificate should:
- Confirm our authorized dealer/distributor status
- Include validity period
- Be on official company letterhead with signature and stamp
- Include any relevant technical support commitments

This authorization is required for tender participation. We would greatly appreciate receiving this at your earliest convenience.

Thank you for your support.

Best regards,
{COMPANY_DETAILS['name']}
{COMPANY_DETAILS.get('email', '')}
{COMPANY_DETAILS.get('phone', '')}
Date: {current_date}
    """
    
    return email_template


@app.route('/')
def index():
    """Render the main application page.
    
    Returns:
        Rendered HTML template for the home page
    """
    return render_template('index.html', company=COMPANY_DETAILS)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle NIT PDF file upload and processing.
    
    This endpoint receives the uploaded PDF file, validates it,
    extracts text, and parses item details.
    
    Returns:
        JSON response with extracted items or error message
    """
    # Check if file is present in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    try:
        # Save uploaded file securely
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(filepath)
        
        # Parse items from extracted text
        items = parse_nit_items(pdf_text)
        
        # Store items in session for later use
        session['items'] = items
        session['pdf_filename'] = filename
        
        return jsonify({
            'success': True,
            'message': 'PDF processed successfully',
            'items': items,
            'item_count': len(items)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500


@app.route('/generate_email', methods=['POST'])
def generate_email():
    """Generate email text based on request type.
    
    Request body should contain:
    - email_type: 'bq_request' or 'oem_authorization'
    - tender_details: dict with tender information (for BQ requests)
    - oem_name: string with OEM name (for OEM authorization)
    
    Returns:
        JSON response with generated email text
    """
    try:
        data = request.json
        email_type = data.get('email_type')
        items = session.get('items', [])
        
        if not items:
            return jsonify({'error': 'No items found. Please upload NIT PDF first'}), 400
        
        email_text = ''
        
        if email_type == 'bq_request':
            tender_details = data.get('tender_details', {})
            email_text = generate_bq_request_email(items, tender_details)
            
        elif email_type == 'oem_authorization':
            oem_name = data.get('oem_name', 'OEM')
            email_text = generate_oem_authorization_email(items, oem_name)
            
        else:
            return jsonify({'error': 'Invalid email type'}), 400
        
        return jsonify({
            'success': True,
            'email_text': email_text,
            'email_type': email_type
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating email: {str(e)}'}), 500


@app.route('/get_items', methods=['GET'])
def get_items():
    """Retrieve currently stored items from session.
    
    Returns:
        JSON response with items list
    """
    items = session.get('items', [])
    return jsonify({
        'success': True,
        'items': items,
        'item_count': len(items)
    })


if __name__ == '__main__':
    # Run the Flask application
    # Debug mode should be disabled in production
    app.run(debug=True, host='0.0.0.0', port=5000)
