from flask_mail import Mail, Message
from flask import current_app

class MailService:
  def __init__(self, app=None):
    """
    Initializes the MailService class and sets up Flask-Mail configuration.
    
    :param app: The Flask app to bind the Mail instance to.
    """ 
    if app is not None:
      self.init_app(app)

  def init_app(self, app):
    """
    Initializes Flask-Mail with the Flask app.
    
    :param app: The Flask app to bind the Mail instance to.
    """
    self.mail = Mail(app)

  def send_mail(self, subject, recipients, body, html=None, sender=None, attachments=None):
    """
    Sends an email using Flask-Mail.
    
    :param subject: Subject of the email.
    :param recipients: List of recipient email addresses.
    :param body: Plain text body of the email.
    :param html: (Optional) HTML body of the email.
    :param sender: (Optional) Sender email address, defaults to Flask app's `MAIL_USERNAME`.
    :param attachments: (Optional) List of attachments to include in the email.
    :return: Result of the email sending process.
    """
    if sender is None:
      sender = current_app.config['MAIL_USERNAME']

    msg = Message(subject=subject,
                  recipients=recipients,
                  body=body,
                  html=html,
                  sender=sender,
                  attachments=attachments)
    
    try:
      self.mail.send(msg)
      return True
    except Exception as e:
      print(f"Error sending email: {str(e)}")
      return False
