from uuid import uuid4
from . import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4().hex), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    image = db.Column(db.Text, nullable=False)
    status = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'image': self.image,
            'status': self.status
        }
    
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4().hex))
    sender = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    receiver = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    chat_id = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    seen = db.Column(db.Boolean, default=False)

    def __init__(self, sender, receiver, content, seen=False):
        self.sender = sender
        self.receiver = receiver
        self.chat_id = self.get_chat_id()
        self.content = content
        self.seen = seen

    def get_chat_id(self):
        return f"{min(self.sender, self.receiver)}_{max(self.sender, self.receiver)}"

    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'sender': self.sender,
            'receiver': self.receiver,
            'content': self.content,
            'sent_at': self.sent_at,
            'seen': self.seen
        }

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.String(255), primary_key=True)
    data = db.Column(db.JSON)
    expiry = db.Column(db.DateTime)

    def __repr__(self):
        return f"<Session {self.id}>"