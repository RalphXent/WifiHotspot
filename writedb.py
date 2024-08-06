""" write to a SQLite database with forms, templates
    add new record, delete a record, edit/update a record
    """

from pathlib import Path
# Dotenv is used to hide sensitive information, like secret_key and database
from dotenv import load_dotenv
import os
import MySQLdb
from flask import Flask, render_template, request, url_for, redirect, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from datetime import datetime

from sqlalchemy.sql import func
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib

# import cx_Oracle      # We are an Oracle shop, and this changes some things
import csv
from io import StringIO       # allows you to store response object in memory instead of on disk

# Create the enviroment_path and load_dotev() with it
env_path = Path('.', '.env')
load_dotenv(dotenv_path=env_path)

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Enter your database connection details below
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

db = SQLAlchemy(app)
# Intialize MySQL
mysql = MySQL(app)

class Cliente(db.Model):
    __tablename__ = 'wifipasillorojo'
    Id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String, nullable=False)
    Email = db.Column(db.String, unique=True, nullable=False)
    Phone_Number = db.Column(db.String, unique=True, nullable=False)
    Date_Created = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    Last_Login = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    Total_Login = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<Cliente {self.Name}>'

@app.route('/')
def index():
    return redirect(url_for('add_record'))

@app.route('/login', methods=['GET', 'POST'])
def add_record():
    if request.method == "POST":
        Name = request.form['Name']
        Email = request.form['Email']
        EmailCheck = Cliente.query.filter_by(Email=Email).first()
        Phone_Number = request.form['Phone_Number']
        Total_Login = 1
        PhoneCheck = Cliente.query.filter_by(Phone_Number=Phone_Number).first()
        if EmailCheck:
            if EmailCheck:
                EmailCheck.Last_Login = datetime.now()
                EmailCheck.Total_Login = EmailCheck.Total_Login + 1
            db.session.commit()
        else:
            record = Cliente(Name=Name, Email=Email, Phone_Number=Phone_Number,Last_Login=datetime.now(), Total_Login=Total_Login)
            db.session.add(record)
            db.session.commit()
        return render_template('server_redirect.html')
    else:
        return render_template('login.html')


@app.route('/portal/login', methods=['GET', 'POST'])
def login_user():
    # Output a message if something goes wrong...
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Retrieve the hashed password
        # hash = password + app.secret_key
        # hash = hashlib.sha1(hash.encode())
        # password = hash.hexdigest()

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return the result
        account = cursor.fetchone()

                # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('main'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
        
        return render_template('portal_login.html', msg=msg)
    else:
        return render_template('portal_login.html')


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/portal/logout')
def logout_user():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login_user'))

@app.route('/portal/principal')
def main():
    if 'loggedin' in session:
        clientes = Cliente.query.all()
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        return render_template('portal_main.html', account=account)
    return redirect(url_for('login_user'))

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for logged in users
@app.route('/portal/clienteswifi')
def clienteswifi():
    # Check if the user is logged in
    if 'loggedin' in session:
        page = request.args.get('page', 1, type=int)
        pagination = Cliente.query.order_by(Cliente.Id).paginate(page=page, per_page=3)
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # User is loggedin show them the home page
        return render_template('portal_wificlients.html', pagination=pagination, account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login_user'))


# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for logged in users
@app.route('/portal/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('portal_profile.html', account=account)
    # User is not logged in redirect to login page
    return redirect(url_for('login_user'))


@app.route('/export/csv', methods=['GET'])
def export():
    si = StringIO()
    cw = csv.writer(si)
    records = Cliente.query.all()   # or a filtered set, of course
    # any table method that extracts an iterable will work
    cw.writerows([(r.Id, r.Name, r.Email, r.Phone_Number, r.Date_Created, r.Last_Login, r.Total_Login) for r in records])
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=report.csv'
    response.headers["Content-type"] = "text/csv"
    return response