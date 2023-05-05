from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'key123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'username': self.username}
    

    def __repr__(self):
        return '<User {}>'.format(self.username)

with app.app_context():
    db.create_all()

@app.route('/users', methods=['POST'])
def create_user():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({'error': 'username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'username already exists'}), 400

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict(), {"message": "user created"}), 201

@app.route('/users/count', methods=['GET'])
def get_user_count():
    user_count = User.query.count()
    return jsonify({'count': user_count})


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token_payload = {'sub': user.id, 'exp': datetime.utcnow() + timedelta(minutes=30)}
    token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
    

    return jsonify({'token': token})

if __name__ == '__main__':
    app.run(debug=True)
