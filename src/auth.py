from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flasgger import swag_from

from .database import db, User

auth = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth.post('/register')
@swag_from('./docs/auth/register.yml')
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if len(password) < 6:
        return jsonify({'error': "Password is too short"}), 400

    if len(username) < 3:
        return jsonify({'error': "User is too short"}), 400

    if not username.isalnum() or " " in username:
        return jsonify({'error': "Username should be alphanumeric, also no spaces"}), 400

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': "Email is taken"}), 409

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'error': "Username is taken"}), 409

    pwd_hash = generate_password_hash(password)

    user = User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': "User created",
        'user': {
            'username': username, "email": email
        }
    }), 200

@auth.post('/login')
@swag_from('./docs/auth/login.yml')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()
    if user:
        if check_password_hash(user.password, password):
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)

            return jsonify({
                "user": {
                    "refresh": refresh,
                    "access": access,
                    "username": user.username,
                    "email": user.email
                }
            }), 200
    return jsonify({"error": "Wrong credentials!"}), 401
    
@auth.get('/me')
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id = user_id).first()
    return jsonify({
        "email": user.email,
        "username": user.username
    }), 200

@auth.get('/token/refresh')
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)
    return jsonify({
        "access": access
    }), 200

