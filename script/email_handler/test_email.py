import logging
from email_handler import EmailHandler

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_email_config():
    # Create email handler instance
    email_handler = EmailHandler()
    
    # Send test email to yourself
    recipient_email = "aikiralyzoltanrudolf@gmail.com"  # Using the same email as sender
    
    print("Sending test email...")
    success = email_handler.send_test_email(recipient_email)
    
    if success:
        print("✅ Test email sent successfully! Check your inbox.")
    else:
        print("❌ Failed to send test email. Check the logs for details.")

if __name__ == "__main__":
    test_email_config()
