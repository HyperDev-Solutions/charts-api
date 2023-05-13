from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import jwt
# from flask_jwt_extended import JWTManager, create_access_token
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_cors import CORS
import pandas as pd
load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app, supports_credentials=True, methods=['GET', 'POST', 'PUT', 'DELETE'])

db = SQLAlchemy(app)
# jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'email': self.email}
    

    def __repr__(self):
        return '<User {}>'.format(self.email)

class UserContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'message': self.message
        }


with app.app_context():
    db.create_all()
    
@app.route('/')
def index():
    return jsonify({'message': 'Hello, World!'})


@app.route('/register', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'email and password are required'}), 400

    email = data['email']
    password = data['password']

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'email already exists'}), 400

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    response = {
        'user': user.to_dict(),
        'message': 'user created'
    }

    return jsonify(response), 201

@app.route('/process-excel' , methods=['GET'])
def process_excel():
    file_path = './ticker_list.xlsx'
    print("file_path", file_path)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        df = pd.read_excel(file_path)
        data = df.to_dict(orient='records')
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'email and password are required'}), 400

    email = data['email']
    password = data['password']

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401
    print(user.id)
    # access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=12))
    access_token = jwt.encode(
                    {"user_id": user.id},
                    app.config["SECRET_KEY"],
                    algorithm="HS256"
                )

    return jsonify({'access_token': access_token, 'message': 'Login successful'})


@app.route('/user-contacts', methods=['POST'])
def create_user_contact():
    data = request.get_json()
    if not data or 'first_name' not in data or 'last_name' not in data or 'email' not in data or 'message' not in data:
        return jsonify({'error': 'first name, last name, email, and message are required'}), 400

    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    message = data['message']

    user_contact = UserContact(first_name=first_name, last_name=last_name, email=email, message=message)
    db.session.add(user_contact)
    db.session.commit()

    # return jsonify(user_contact.to_dict(), {"message": "Your message is received"}), 201
    response = {
        'user': user_contact.to_dict(),
        'message': 'Your message is received'
    }
    return jsonify(response), 201



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
