from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4
from .models import User, Message
from . import db
from . import mail_service
from .libraries.image import Image


bp = Blueprint('routes', __name__)


@bp.route('/auth/get_started', methods=['POST'])
def get_started():
  data = request.get_json()
  email = data.get('email')

  if not email:
    return jsonify({"error": "Email is required"}), 400
  
  existing_user = User.query.filter_by(email=email).first()

  if existing_user:
    return jsonify({"error": "Email is already registered"}), 400
  
  session['email'] = email

  client_url = current_app.config['CLIENT_URL']
  registration_link = f"{client_url}/register?email={email}"
  html = f"""
    <html>
      <body>
        <h1>Welcome to Our Service</h1>
        <p>We are excited to have you on board!</p>
        <a href="{registration_link}">Click here to register</a>
      </body>
    </html>
  """

  try:
    success = mail_service.send_mail(
      subject="Welcome to our service!",
      recipients=[email],
      body="Please check your email to complete the registration process.",
      html=html
    )
    if success:
      return jsonify({"message": "Mail Sent Successfully"}), 200
    else:
      return jsonify({'error': 'Error occurred while sending mail'}), 500
  except Exception as e:
    return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@bp.route('/auth/register', methods=['POST'])
def register():
    session_email = session.get('email')

    data = request.get_json()
    email = data.get('email').strip()
    if not email:
        return jsonify({"error": "Please enter email"}), 400
    
    if email != session_email:
        return jsonify({"error": "Email does not match email, where we sent you this webpage URL", "session_email": session_email, "email": email}), 400

    username = data.get('username').strip()
    password = data.get('password').strip()

    if not username:
        return jsonify({"error": "Please enter username"}), 400
    
    if not password:
        return jsonify({"error": "Please enter password"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email is already registered"}), 400

    hashed_password = generate_password_hash(password)

    id = uuid4().hex
    user = User(id=id, username=username, email=email, password=hashed_password)

    image_instance = Image()
    default_image_path = image_instance.get_default_image_path()

    upload_result = image_instance.upload_to_cloudinary(default_image_path, user_id=str(user.id))

    if not upload_result:
        return jsonify({"error": "Failed to upload default image"}), 500

    user.image = upload_result['secure_url']

    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id
    session.pop('email', None)

    return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 200

@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email').strip()
    password = data.get('password').strip()

    if not email: 
        return jsonify({"error": "Please enter email"}), 400
    if not password:
        return jsonify({"error": "Please enter password"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Email not registered"}), 400
    if not check_password_hash(user.password, password):
        return jsonify({"error": "Wrong Password"}), 400
    

    session['user_id'] = user.id

    return jsonify({"message": "Login successful"}), 200

@bp.route('/home/get_data', methods=['GET'])
def get_data():
    if 'user_id' not in session:
        return jsonify({"error": "Auth failed"}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.status:
        user.status = True
        db.session.commit()

    subquery = (
        db.session.query(
            Message.chat_id,
            db.func.max(Message.sent_at).label('latest_sent_at')
        )
        .filter((Message.sender == user.id) | (Message.receiver == user.id))
        .group_by(Message.chat_id)
        .subquery()
    )

    latest_messages = (
        db.session.query(Message)
        .join(subquery, (Message.chat_id == subquery.c.chat_id) & (Message.sent_at == subquery.c.latest_sent_at))
        .order_by(Message.sent_at.desc())
        .all()
    )

    return_data = {
        'user': user.to_dict(),
        'chats': []
    }

    for chat in latest_messages:
        other_user_id = chat.receiver if chat.sender == user.id else chat.sender
        other_user = User.query.get(other_user_id)

        last_message = chat

        return_data['chats'].append({
            'id': chat.chat_id,
            'current_user': user.id,
            'current_user_name': user.username,
            'other_user_id': other_user.id if other_user else None,
            'updated_at': chat.sent_at,
            'sender': user.username if chat.sender == user.id else other_user.username,
            'other_user': {
                'id': other_user.id if other_user else None,
                'username': other_user.username if other_user else None,
                'email': other_user.email if other_user else None,
                'image': other_user.image if other_user else None
            },
            'last_message': last_message.content if last_message else None,
            'seen': last_message.seen if last_message else None
        })

    return jsonify(return_data), 200


@bp.route('/auth/logout', methods=['GET'])
def logout():
    if 'user_id' not in session:
        return jsonify({"message": "No active session"}), 400

    user_id = session['user_id']

    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    user.status = False
    db.session.commit()

    session.pop('user_id', '')
    return jsonify({"message": "Logged out successfully"}), 200


@bp.route('/home/search', methods=['POST'])
def search(): 
    if 'user_id' not in session:
        return jsonify({"error": "Auth failed"}), 401

    data = request.get_json()
    query = data.get('query').strip()
    if not query:
        return jsonify({"error": "Searched users will appear here..."}), 400

    users = User.query.filter(
        (User.username.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
    ).all() 

    if not users:
        return jsonify({"message": "No users found"}), 404

    user_list = [user.to_dict() for user in users]
    return jsonify(user_list), 200


@bp.route('/home/get_chat', methods=['POST'])
def get_chat():
    if 'user_id' not in session:
        return jsonify({"error": "Auth failed"}), 401
    
    data = request.get_json()
    chat_id = data.get('chat_id', '').strip()
    
    if not chat_id:
        return jsonify({"error": "No chat provided"}), 400
    
    user_id = session['user_id']

    other_user_id = None

    try:
        # Split the chat_id to get the two user IDs
        user1, user2 = chat_id.split('_')

        # Check if the user is trying to chat with themselves
        if user1 == user2:
            return jsonify({"error": "You cannot chat with yourself"}), 403
        
        # Ensure the user is part of the chat
        if user1 != user_id and user2 != user_id:
            return jsonify({"error": "You are not in this chat"}), 403
        
        other_user_id = user2 if user1 == user_id else user1

    except ValueError:
        return jsonify({"error": "Invalid chat_id format"}), 400
    
    other_user = User.query.get(other_user_id)
    if not other_user:
        return jsonify({"error": "User not found"}), 404
    
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.sent_at).all()
    message_list = [
        {
            'id': msg.id,
            'sender': msg.sender,
            'receiver': msg.receiver,
            'content': msg.content,
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
            'seen': msg.seen
        }
        for msg in messages
    ]
    
    return jsonify({
            "chat_id": chat_id,
        "other_user": {
            "id": other_user.id,
            "email": other_user.email,
            "username": other_user.username,
            "image": other_user.image,
            "status": other_user.status
        },
        "messages": message_list
    }), 200


@bp.route('/home/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({"error": "Auth failed"}), 401

    data = request.get_json()
    if not data.get('content') or not data.get('sender') or not data.get('receiver'):
        return jsonify({"error": "Missing required fields"}), 400


    try:
        message = Message(
            sender=data.get('sender'),
            receiver=data.get('receiver'),
            content=data.get('content'),
        )

        db.session.add(message)
        db.session.commit()

        return jsonify({"message": "Message sent successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@bp.route('/home/seen_chat', methods=['POST'])
def seen_chat():
    if 'user_id' not in session:
        return jsonify({"error": "Auth failed"}), 401

    data = request.get_json()
    chat_id = data.get('chat_id', '').strip()

    if not chat_id:
        return jsonify({"error": "No chat provided"}), 400

    user_id = session['user_id']

    unseen_messages = Message.query.filter_by(chat_id=chat_id, receiver=user_id, seen=False).all()

    if not unseen_messages:
        return jsonify({"message": "No unseen messages"}), 200

    for message in unseen_messages:
        message.seen = True

    db.session.commit()

    return jsonify({"message": "Chat marked as seen"}), 200

@bp.route('/test_session')
def test_session():
    session['test'] = 'This is a test'
    return jsonify({"message": "Session set: " + session.get('test')})

@bp.route('/get_session')
def get_session():
    test_value = session.get('test')
    return jsonify({"test_value": test_value})