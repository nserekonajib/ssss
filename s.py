import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Email configuration
GMAIL_USER = "nserekonajib3@gmail.com"
GMAIL_APP_PASSWORD = "bkri kfbo bwxj iyow"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def validate_email_address(email):
    """Validate email address format"""
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError as e:
        logger.error(f"Invalid email: {email} - {str(e)}")
        return None

def send_email(recipient, subject, body, sender_name=None, cc=None, bcc=None, attachments=None):
    """
    Send email using Gmail SMTP
    
    Args:
        recipient (str or list): Email recipient(s)
        subject (str): Email subject
        body (str): Email body (can be HTML)
        sender_name (str): Optional sender display name
        cc (list): CC recipients
        bcc (list): BCC recipients
        attachments (list): List of file paths to attach
    
    Returns:
        tuple: (success, message)
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        
        # Set sender
        if sender_name:
            msg['From'] = f"{sender_name} <{GMAIL_USER}>"
        else:
            msg['From'] = GMAIL_USER
        
        # Set recipients
        if isinstance(recipient, list):
            msg['To'] = ', '.join(recipient)
        else:
            msg['To'] = recipient
        
        msg['Subject'] = subject
        
        # Handle CC
        if cc:
            if isinstance(cc, list):
                msg['Cc'] = ', '.join(cc)
            else:
                msg['Cc'] = cc
        
        # Handle BCC (added later in send process)
        
        # Attach body
        if '<html>' in body or '<body>' in body:
            part = MIMEText(body, 'html')
        else:
            part = MIMEText(body, 'plain')
        msg.attach(part)
        
        # Handle attachments
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        attachment = MIMEApplication(f.read())
                        attachment.add_header(
                            'Content-Disposition', 
                            'attachment', 
                            filename=os.path.basename(file_path)
                        )
                        msg.attach(attachment)
        
        # Prepare all recipients for sending
        all_recipients = []
        if isinstance(recipient, list):
            all_recipients.extend(recipient)
        else:
            all_recipients.append(recipient)
        
        if cc:
            if isinstance(cc, list):
                all_recipients.extend(cc)
            else:
                all_recipients.append(cc)
        
        if bcc:
            if isinstance(bcc, list):
                all_recipients.extend(bcc)
            else:
                all_recipients.append(bcc)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg, to_addrs=all_recipients)
        
        logger.info(f"Email sent successfully to: {all_recipients}")
        return True, "Email sent successfully"
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failed. Check your Gmail credentials.")
        return False, "Authentication failed. Please check your email credentials."
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False, f"Error sending email: {str(e)}"

@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'message': 'Email API is running',
        'version': '1.0.0'
    })

@app.route('/send-email', methods=['POST'])
def send_email_endpoint():
    """
    Endpoint to send emails
    
    Expected JSON payload:
    {
        "to": "recipient@example.com" or ["recipient1@example.com", "recipient2@example.com"],
        "subject": "Email Subject",
        "body": "Email content (plain text or HTML)",
        "sender_name": "Optional Sender Name",  // optional
        "cc": "cc@example.com" or ["cc1@example.com", "cc2@example.com"],  // optional
        "bcc": "bcc@example.com" or ["bcc1@example.com", "bcc2@example.com"]  // optional
    }
    """
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'to' not in data:
            return jsonify({'error': 'Recipient (to) is required'}), 400
        
        if 'subject' not in data:
            return jsonify({'error': 'Subject is required'}), 400
        
        if 'body' not in data:
            return jsonify({'error': 'Body is required'}), 400
        
        # Validate email addresses
        recipients = data['to']
        if isinstance(recipients, list):
            for email in recipients:
                if not validate_email_address(email):
                    return jsonify({'error': f'Invalid email address: {email}'}), 400
        else:
            if not validate_email_address(recipients):
                return jsonify({'error': f'Invalid email address: {recipients}'}), 400
        
        # Validate CC if provided
        if 'cc' in data and data['cc']:
            cc_list = data['cc']
            if isinstance(cc_list, list):
                for email in cc_list:
                    if not validate_email_address(email):
                        return jsonify({'error': f'Invalid CC email: {email}'}), 400
            else:
                if not validate_email_address(cc_list):
                    return jsonify({'error': f'Invalid CC email: {cc_list}'}), 400
        
        # Validate BCC if provided
        if 'bcc' in data and data['bcc']:
            bcc_list = data['bcc']
            if isinstance(bcc_list, list):
                for email in bcc_list:
                    if not validate_email_address(email):
                        return jsonify({'error': f'Invalid BCC email: {email}'}), 400
            else:
                if not validate_email_address(bcc_list):
                    return jsonify({'error': f'Invalid BCC email: {bcc_list}'}), 400
        
        # Send email
        success, message = send_email(
            recipient=data['to'],
            subject=data['subject'],
            body=data['body'],
            sender_name=data.get('sender_name'),
            cc=data.get('cc'),
            bcc=data.get('bcc')
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/send-email-simple', methods=['POST'])
def send_simple_email():
    """
    Simpler endpoint for basic email sending
    
    Expected JSON payload:
    {
        "to": "recipient@example.com",
        "subject": "Email Subject",
        "body": "Email content"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('to', 'subject', 'body')):
            return jsonify({'error': 'Missing required fields: to, subject, body'}), 400
        
        # Validate email
        if not validate_email_address(data['to']):
            return jsonify({'error': 'Invalid email address'}), 400
        
        # Send email
        success, message = send_email(
            recipient=data['to'],
            subject=data['subject'],
            body=data['body']
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)