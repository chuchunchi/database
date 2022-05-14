import os
from flask import Flask, render_template, session, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import mysql.connector
import time

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
cursor = db.cursor(buffered=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def hello():
    uid = session.get('uid', None)
    if uid is not None:
        session.pop('uid')
    session['uid'] = 2
    return render_template('index.html')


@app.route('/main', methods=['GET'])
def main():
    uid = session.get('uid')
    userShop = None
    userShopItems = list()
    if uid is not None:
        cursor.execute("select shopname, shoptype, latitude, longitude, sid from shop where uid = %s", (uid, ))
        res = cursor.fetchall()
        if len(res) > 0:
            tmp = res[0]
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


@app.route('/validateShopInfo', methods=['POST'])
def validateShopInfo():
    def check_num(x, s):
        try:
            a = float(x)
            if s == 'longitude':
                if a > 180.0 or a < -180.0:
                    return False
            else:
                if a > 90.0 or a < -90.0:
                    return False
            return True
        except ValueError:
            return False

    shopName = request.form.get('name')
    shopType = request.form.get('type')
    longitude = request.form.get('longitude')
    latitude = request.form.get('latitude')
    if shopName + shopType + longitude + latitude == '':
        return jsonify({'error': True})
    cursor.execute("select * from shop where shopname = %s", (shopName, ))
    res = cursor.fetchall()
    result = dict()
    result['nameResult'] = 'This Name is used!' if len(res) > 0 else \
        'Shop Name should be at least one character!' if shopName == '' else ''
    result['typeResult'] = 'Shop Name should longer than 0' if shopType == '' else ''
    result['longitudeResult'] = 'Longitude format Error' if check_num(longitude, 'longitude') is False else ''
    result['latitudeResult'] = 'Latitude format Error' if check_num(latitude, 'latitude') is False else ''
    result['error'] = False if result['nameResult'] + result['typeResult'] + result['longitudeResult'] + \
        result['latitudeResult'] == '' else True
    return jsonify(result)


@app.route('/registerShop', methods=['POST'])
def registerShop():
    uid = session.get('uid')
    cursor.execute("select shopname from shop where uid = %s", (uid,))
    r = cursor.fetchall()
    if len(r) == 0:
        shopName = request.form.get('shopName')
        shopType = request.form.get('shopType')
        longitude = request.form.get('shopLongitude')
        latitude = request.form.get('shopLatitude')
        cursor.execute("""insert into shop (uid, shopname, shoptype, latitude, longitude, location)
                            values (%s, %s, %s, %s, %s, ST_GeomFromText(%s));"""
                       , (uid, shopName, shopType, latitude, longitude, f'POINT({latitude} {longitude})',))
        db.commit()
    flash("Successfully Registered.", category='success')
    return redirect(url_for('main'))


@app.route('/validateItemInfo', methods=['POST'])
def validateItemInfo():
    def check_num(x):
        try:
            a = int(x)
            if a > 0:
                return True
            else:
                return False
        except ValueError:
            return False

    itemName = request.form.get('name')
    itemPrice = request.form.get('price')
    itemQuantity = request.form.get('quantity')
    picLength = request.form.get('pic')

    if itemName + itemPrice + itemQuantity == '' and picLength == '0':
        return jsonify({'error': True})

    result = dict()
    result['nameResult'] = 'Food Name should be at least one character!' if itemName == '' else ''
    result['priceResult'] = 'Price format Error' if check_num(itemPrice) is False else ''
    result['quantityResult'] = 'Quantity format Error' if check_num(itemQuantity) is False else ''
    result['picResult'] = 'Please select a file' if picLength == '0' else ''
    result['error'] = False if result['nameResult'] + result['priceResult'] + result['quantityResult'] + \
        result['picResult'] == '' else True
    return jsonify(result)


@app.route('/registerItem', methods=['POST'])
def registerItem():
    uid = session.get('uid')
    cursor.execute("select sid from shop where uid = %s", (uid,))
    sid = cursor.fetchall()[0][0]
    itemName = request.form.get('itemName')
    itemPrice = request.form.get('itemPrice')
    itemQuantity = request.form.get('itemQuantity')
    pic = request.files['itemPic']
    if allowed_file(pic.filename) is False:
        flash('Incapable file', category='danger')
        return redirect(url_for('main'))
    picName = secure_filename(pic.filename)
    fileName = str(time.time_ns()) + '.' + picName.rsplit('.', 1)[1].lower()
    pic.save(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], fileName))
    cursor.execute("""insert into item (sid, name, quantity, price, image) VALUES (%s, %s, %s, %s, %s)""",
                   (sid, itemName, itemQuantity, itemPrice, fileName))
    db.commit()
    flash("Add success!", category='success')
    return redirect(url_for('main'))


@app.route('/updateItem', methods=['POST'])
def updateItem():
    def check_num(x):
        try:
            a = int(x)
            if a <= 0:
                return False
            return True
        except ValueError:
            return False
    itemId = request.form.get('itemId')
    itemQuantity = request.form.get('Quantity')
    itemPrice = request.form.get('Price')
    if check_num(itemQuantity) and check_num(itemPrice):
        cursor.execute("UPDATE item SET quantity = %s, price = %s WHERE iid = %s", (itemQuantity, itemPrice, itemId, ))
        db.commit()
        flash('Update Success!', category='success')
    elif itemQuantity == '' or itemPrice == '':
        flash('Update Error! Input is Empty.', category='danger')
    else:
        flash('Update Error! Input format Error.', category='danger')
    return redirect(url_for('main'))


@app.route('/deleteItem', methods=['POST'])
def deleteItem():
    itemId = request.form.get('itemId')
    cursor.execute("SELECT image FROM item where iid = %s", (itemId, ))
    fileName = cursor.fetchall()[0][0]
    cursor.execute("DELETE FROM item where iid = %s", (itemId, ))
    os.remove(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], fileName))
    db.commit()
    flash('Delete Success.', category='success')
    return redirect(url_for('main'))


if __name__ == "__main__":
    app.run(debug=True)