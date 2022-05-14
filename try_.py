# -*- coding: utf-8 -*-
"""
Created on Wed May 11 23:58:46 2022

@author: chuch
"""


from markupsafe import escape
from flask import Flask, render_template, session, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import mysql.connector

UPLOAD_FOLDER = 'static\\Picture'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app = Flask(__name__)
app.config['SECRET_KEY'] = b'S\xc5\xf5\xf4!\x9d=S\t\xb4\xb8\xcb\xb5\x16\x1cfXj\xde\x85\xe7\xf5\xe4\xe2'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
SESSION_TYPE = 'redis'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="0801",
    database="db"
)
cursor = db.cursor()


@app.route('/')
def hello():
    return render_template('index.html')
@app.route('/main', methods=['GET'])
def main():
    uid = session.get('uid')
    userShop = None
    if uid is not None:
        cursor.execute("select shopname, shoptype, latitude, longitude, sid from shop where uid = %s", (uid, ))
        tmp = cursor.fetchone()
        if tmp is not None:
            userShop = {
                'shopName': tmp[0],
                'shopType': tmp[1],
                'latitude': tmp[2],
                'longitude': tmp[3]
            }
            sid = tmp[4]
            cursor.execute("select name, price, quantity, image, iid from item where sid = %s", (sid, ))
            userShopItems = cursor.fetchall()
    return render_template('nav.html', userShop=userShop, userShopItems=userShopItems)

@app.route('/sign-up.html', methods=('GET', 'POST'))
def register():
    if request.method=='POST':
        name = request.form.get('name')
        password = request.form.get('password')
        phonenumber = request.form.get('phonenumber')
        Account = request.form.get('Account')
        re_password = request.form.get('re-password')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        error = None
        if name=='':
            error = 'Username is required.'
        elif phonenumber=='':
            error = 'phonenumber is required.'
        elif Account=='':
            error = 'account is required.'
        elif password=='':
            error = 'Password is required.'
        elif re_password=='':
            error = 're-type Password is required.'
        elif latitude=='':
            error = 'latitude is required.'
        elif longitude=='':
            error = 'longitude is required.'
        elif password!=re_password:
            error = 're-type password does not match'
        elif password.isalnum()==False or Account.isalnum()==False:
            error = 'Account and password format error'
        elif phonenumber.isdigit()==False or len(phonenumber)==10:
            error = 'phonenumber format error'
        else:
            try:
                float(latitude)
                float(longitude)
            except ValueError:
                error = 'wrong latitude/longtitude format'
            
        if error is None:
            try:
                cursor.execute(
                    "INSERT INTO user (name, password,account,phone,latitude,longitude) VALUES (%s,%s,%s,%d,%f,%s)",
                    (name, generate_password_hash(password),Account,phonenumber,latitude,longitude),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {name} is already registered."
            else:
                return redirect(url_for('main'))
        print(error)
        flash(error)
    return render_template('sign-up.html')

@app.route('/index.html', methods=('GET', 'POST'))
def login():
    if request.method=='POST':
        Account = request.form.get('Account')
        password = request.form.get('password')
        error = None
        cursor.execute('SELECT * FROM user WHERE account = %s', (Account,))
        accountdata = cursor.fetchone()
        if accountdata is None:
            error = 'Account not register'
        elif not check_password_hash(accountdata[0][2], password):
            error = 'Incorrect password.'
        if error is None:
            session.clear()
            session['uid'] = accountdata[0][0]
            return redirect(url_for('main'))
    
        flash(error)
        print(error)
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)