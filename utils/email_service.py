import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt
from config import JWT_SECRET

class EmailService:
    def __init__(self):
        self.host = os.getenv('EMAIL_HOST')
        self.port = int(os.getenv('EMAIL_PORT'))
        self.username = os.getenv('EMAIL_USER')
        self.password = os.getenv('EMAIL_PASSWORD')

    def _create_connection(self):
        try:
            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.username, self.password)
            return server
        except Exception as e:
            print(f"Failed to create SMTP connection: {str(e)}")
            return None

    def send_email(self, to_email, subject, body):
        message = MIMEMultipart()
        message['From'] = self.username
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'html'))

        try:
            server = self._create_connection()
            if server:
                server.send_message(message)
                server.quit()
                return True
            return False
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

def send_password_reset(email):
    try:
        reset_token = jwt.encode(
            {'email': email, 'type': 'password_reset'},
            JWT_SECRET,
            algorithm='HS256'
        )
        
        reset_link = f"http://yourdomain.com/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_link}">Reset Password</a>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """

        
        email_service = EmailService()
        success = email_service.send_email(
            to_email=email,
            subject="Password Reset Request",
            body=html_content
        )
        
        return success
    except Exception as e:
        print(f"Error in send_password_reset: {str(e)}")
        return False