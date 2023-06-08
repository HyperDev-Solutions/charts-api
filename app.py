from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import jwt
# from flask_jwt_extended import JWTManager, create_access_token
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_cors import CORS
import pandas as pd
#Importing Libraries
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import yahoo_fin.stock_info as si
from pytictoc import TicToc
import numpy as np
import matplotlib.pyplot as plt
import stumpy
import json
load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app, supports_credentials=True, methods=['GET', 'POST', 'PUT', 'DELETE'])

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50) , nullable=False)
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
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'message': self.message
        }
        
class WaitingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False)
    fullname = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'fullname': self.fullname
        }



with app.app_context():
    db.create_all()
    
@app.route('/')
def index():
    return jsonify({'message': 'Hello, World!'})


@app.route('/register', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data or 'username' not in data:
        return jsonify({'error': 'email, username, and password are required'}), 400

    username = data['username']
    email = data['email']
    password = data['password']

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'email already exists'}), 400
   

    user = User(email=email, username=username)
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
                    {"user_id": user.id, "email": user.email, "exp": datetime.utcnow() + timedelta(hours=12)},
                    app.config["SECRET_KEY"],
                    algorithm="HS256"
                )

    return jsonify({'access_token': access_token, 'message': 'Login successful'})


@app.route('/user-contacts', methods=['POST'])
def create_user_contact():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'message' not in data:
        return jsonify({'error': 'username, email, and message are required'}), 400

    username = data['username']
    email = data['email']
    message = data['message']

    user_contact = UserContact(username=username, email=email, message=message)
    db.session.add(user_contact)
    db.session.commit()

    # return jsonify(user_contact.to_dict(), {"message": "Your message is received"}), 201
    response = {
        'user': user_contact.to_dict(),
        'message': 'Your message is received'
    }
    return jsonify(response), 201

@app.route('/waiting-list', methods=['POST'])
def add_to_waiting_list():
    data = request.get_json()
    if not data or 'email' not in data or 'fullname' not in data:
        return jsonify({'error': 'email and fullname are required'}), 400

    email = data['email']
    fullname = data['fullname']

    waiting_entry = WaitingList(email=email, fullname=fullname)
    db.session.add(waiting_entry)
    db.session.commit()

    response = {
        'data': waiting_entry.to_dict(),
        'message': 'Joined to the waiting list'
    }

    return jsonify(response), 201

@app.route('/static/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(os.path.join(root_dir, 'static'), filename)

@app.route('/graph/<path:ticker>')
def get_graph(ticker):
    Analyzed_ticker = ticker
    t=TicToc()
    #Defining Start and End Date
    end_date = date.today().strftime('%m/%d/%Y') #'01/01/2023'
    #start_date = '01/01/2010'
    start_date = '01/01/1990'
    #Importing Data.  La part AAPL serveix per poder mirar contra altres patterns, a part de la propia.  Caldria fer bucle i agafar les millors

    #today = date.today()
    sel_start = (date.today() - relativedelta(months=5))
    #print(sel_start)

    #ticker_list = ['^STOXX50E', 'cat', 'cop', 'xom', 'v', 'jpm', 'wfc', 'lvs', 'f', 'ups', 'unp', 'ELE.MC', 'ITX.MC', 'DUK', 'o', 'LIN']
    #add_list = [5, 20, 40]
    add_list = [30]
    ticker_list = ['^GSPC']

    for ticker in ticker_list:
        for add in add_list:
            #mestre
            master_ticker = si.get_data(Analyzed_ticker, start_date = start_date , end_date = end_date)["close"].to_frame().round(1)
            master_ticker.head()
            master_ticker["1DMA"] = master_ticker["close"].rolling(1).mean().round(1)
            master_ticker["5DMA"] = master_ticker["close"].rolling(5).mean().round(1)
            master_ticker = master_ticker.dropna()

            #Comparat
            compared_ticker =si.get_data(ticker, start_date = start_date , end_date = end_date)["close"].to_frame().round(1)
            compared_ticker.head()
            compared_ticker["1DMA"] = compared_ticker["close"].rolling(1).mean().round(1)
            compared_ticker["5DMA"] = compared_ticker["close"].rolling(5).mean().round(1)
            compared_ticker = compared_ticker.dropna()

            #Partitioning the data
            #sel_start = date(2022,8,1)
            master_data = master_ticker[sel_start:end_date]
            #print(master_data.head())
            compared_data = compared_ticker[:sel_start]
            #print(compared_data.tail())
            #print(compared_data)

            #Calculating distance profile
            distance_profile = stumpy.mass(master_data["1DMA"], compared_data["1DMA"],normalize=True)
            #Getting index position with the minimum distance score
            idx = np.argmin(distance_profile)
            #print(f"The nearest pattern to {ticker} is the period between {str(compared_data.iloc[idx].name.strftime('%m/%d/%Y'))} and {str(compared_data.iloc[idx+len(master_data)].name.strftime('%m/%d/%Y'))} of {ticker}")

            # Since MASS computes z-normalized Euclidean distances, we should z-normalize our subsequences before plotting
            master_data_z_norm = stumpy.core.z_norm(master_data["1DMA"].values)
            mostra_i = len(master_data)
            compared_data_z_norm = stumpy.core.z_norm(compared_data["1DMA"].values[idx:idx+len(master_data)+add])


            #Top 10 matches
            matches = stumpy.match(master_data["1DMA"],compared_data["1DMA"],max_matches=10,normalize= True)
            #print(matches)
            matches_df= pd.DataFrame(matches, columns=["Score","Position"])
            a=[]
            cv_list=[]
            fc_list=[]
            returns=[]
            pos=[]
            pos = matches_df["Position"]


            #print(pos)
            for i in matches_df["Position"]:
                try:
                    close_value = compared_data.iloc[i+mostra_i].loc['close']
                    cv_list.append(close_value)
                except:
                    cv_list.append(0)

                try:
                    future_close = compared_data.iloc[i + mostra_i + add].loc['close']
                    fc_list.append(future_close)
                except:
                    fc_list.append(0)

                try:
                    rets = (compared_data.iloc[i + mostra_i + add].loc['close'] / compared_data.iloc[i + mostra_i].loc['close']) - 1
                    returns.append(rets)
                except:
                    returns.append(0)
                x = compared_data.iloc[i].name.strftime('%m/%d/%Y')
                a.append(x)
            matches_df["Match_Start_Dates"]= a
            matches_df["Norm_Score"] = (matches_df["Score"]-matches_df["Score"].mean())/matches_df["Score"].std()
            matches_df["Ini_CValue"] = cv_list
            matches_df["Fin_CValue"] = fc_list
            matches_df["Returns"] = returns
            matches_df["tck"] = ticker
            matches_df["add"] = add
            #print(matches_df)
            print("matches_df",matches_df,"master_data_z_norm",master_data_z_norm,"compared_data_z_norm",compared_data_z_norm)
            matches_df_filled = matches_df.fillna(value=0)
            compared_data_filled = compared_data.fillna(value=0)
            data = {
                "matches_df":matches_df_filled.to_dict(orient='records'),
                "master_data_z_norm":master_data_z_norm.tolist(),
                "compared_data_z_norm":compared_data_z_norm.tolist(),
                "compared_data":compared_data_filled.to_dict(orient='records')
            }
            json_data = json.dumps(data)

            return jsonify(json_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
