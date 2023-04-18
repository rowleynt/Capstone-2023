from flask import Flask, render_template, request, redirect, url_for, session # -> pip install flask
from werkzeug.utils import secure_filename
import datetime
import sqlite3
import re
import os
import bcrypt  # need to manually install -> pip install bcrypt


app = Flask(__name__)
if not os.path.exists(os.path.join('static', 'media')):
    os.mkdir('static')
    os.mkdir('static/media')
UPLOAD_FOLDER = os.path.join('static', 'media')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png"]

SALT = b'$2b$12$xupBDilwoxEyd/vXNsmNSO' # storing salt here is probably very bad; fix?

app.secret_key = 'qm$Fx%tvPpGi?k+/32iiRL-v??o)wJLtE@1/Z$u-%)#4ia~sc'

# initial database stuff
db = sqlite3.connect("boomtown.db")
conn = db.cursor()
conn.execute("CREATE TABLE IF NOT EXISTS Agent (agentID INTEGER PRIMARY KEY AUTOINCREMENT, agentFName TEXT, agentLName TEXT, email TEXT, password TEXT, phone TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS Property (propertyID INTEGER PRIMARY KEY AUTOINCREMENT, agentID INTEGER, type TEXT, size TEXT, numBeds INTEGER, numBaths INTEGER, address TEXT, FOREIGN KEY (agentID) REFERENCES Agent (agentID))")
conn.execute("CREATE TABLE IF NOT EXISTS Guest (guestID INTEGER PRIMARY KEY AUTOINCREMENT, propertyID INTEGER, guestFName TEXT, guestLName TEXT, guestEmail TEXT, phone TEXT, dateOfVisit TEXT, FOREIGN KEY (propertyID) REFERENCES Property (propertyID))")
db.commit()
conn.close()
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password_plaintext = request.form['password']
        password_hash = gen_safe_password(password_plaintext)

        # TODO: fix this line (causes crash if account not in db)
        account = db_select(f'SELECT * FROM Agent WHERE email = "{email}" AND password = "{password_hash}"')
        if account:
            session['loggedin'] = True
            session['email'] = email
            session['fname'] = account[0][1]
            session['lname'] = account[0][2]
            session['phone'] = account[0][5]
            session['agentID'] = account[0][0]
            msg = 'Logged in successfully'
            return redirect(url_for('admin_portal'))
        else:
            msg = 'Incorrect email / password'
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'agentFName' in request.form and 'agentLName' in request.form and 'email' in request.form and 'password' in request.form and 'email' in request.form and 'phone' in request.form:
        email = request.form['email']

        unsafe_password = request.form['password']
        safe_password = gen_safe_password(unsafe_password)

        fname = request.form['agentFName']
        lname = request.form['agentLName']
        phone = request.form['phone']
        account = db_select(f'SELECT * FROM Agent WHERE email = "{email}"')
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address'
        elif not fname or not lname or not phone or not unsafe_password or not email:
            msg = 'Please fill out the form'
        else:
            session['loggedin'] = True
            session['email'] = email
            session['fname'] = fname
            session['lname'] = lname
            session['phone'] = phone
            db_insert(f'INSERT INTO Agent (agentFName, agentLName, email, password, phone) VALUES ("{fname}", "{lname}", "{email}", "{safe_password}", "{phone}")')
            aID = db_select(f'SELECT agentID FROM Agent WHERE email = "{email}"')
            session['agentID'] = aID[0][0]

            os.mkdir(os.path.join(UPLOAD_FOLDER, str(aID[0][0])))
            os.mkdir(os.path.join(UPLOAD_FOLDER, str(aID[0][0]), "AGENT"))
            os.mkdir(os.path.join(UPLOAD_FOLDER, str(aID[0][0]), "PROPERTY"))

            msg = 'Logged in successfully'
            return redirect(url_for('admin_portal'))
    elif request.method == 'POST':
        msg = 'Please fill out the form'
    return render_template('register.html', msg=msg)


@app.route("/portal", methods=["GET", "POST"])
def admin_portal():
    if session.get('loggedin'):
        prop_list = db_select(f"SELECT * FROM Property WHERE agentID = {session['agentID']}")
        if request.method == "POST":
            if 'profileimg' not in request.files:
                render_template('index.html', user_image=os.path.join(app.config['UPLOAD_FOLDER'], str(session['agentID']), "AGENT", 'default.png'), list=prop_list)
            file = request.files['profileimg']
            path = os.path.join(app.config['UPLOAD_FOLDER'], str(session['agentID']), "AGENT", "default.png")
            file.save(path)
            return render_template('index.html', user_image=path, list=prop_list)
        else:
            return render_template('index.html', user_image=os.path.join(app.config['UPLOAD_FOLDER'], str(session['agentID']), "AGENT", 'default.png'), list=prop_list)
    else:
        return redirect(url_for('login'))


@app.route("/updateinfo", methods=["GET", "POST"])
def update_profile():
    if session.get('loggedin'):
        if request.method == "POST":
            fname = request.form.get('agentFName')
            lname = request.form.get('agentLName')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')
            if fname:
                db_insert(f'UPDATE Agent SET agentFName = "{fname}" WHERE agentID = {session["agentID"]}')
                session.pop('fname')
                session['fname'] = fname
            if lname:
                db_insert(f'UPDATE Agent SET agentLName = "{lname}" WHERE agentID = {session["agentID"]}')
                session.pop('lname')
                session['lname'] = lname
            if email:
                db_insert(f'UPDATE Agent SET email = "{email}" WHERE agentID = {session["agentID"]}')
                session.pop('email')
                session['email'] = email
            if password:
                db_insert(f'UPDATE Agent SET agentFName = "{password}" WHERE agentID = {session["agentID"]}')
            if phone:
                db_insert(f'UPDATE Agent SET agentFName = "{phone}" WHERE agentID = {session["agentID"]}')
                session.pop('phone')
                session['phone'] = phone
            return redirect(url_for('admin_portal'))
        else:
            return render_template('updateinfo.html')
    else:
        return redirect(url_for('login'))


@app.route("/addproperty", methods=["GET", "POST"])
def add_property():
    if session.get('loggedin'):
        if request.method == "POST":
            propSize = request.form.get('propertySize')
            propType = request.form.get('propertyType')
            numBeds = int(request.form.get('numBeds'))
            numBaths = int(request.form.get('numBaths'))
            address = request.form.get('address')
            currAgent = int(session.get('agentID'))
            db_insert(f'INSERT INTO Property (agentID, type, size, numBeds, numBaths, address) VALUES ({currAgent}, "{propType}", "{propSize}", {numBeds}, {numBaths}, "{address}")')
            prop_id = db_select(f'SELECT propertyID FROM Property')[-1][0]
            os.mkdir(os.path.join(UPLOAD_FOLDER, str(session['agentID']), "PROPERTY", str(prop_id)))
            return redirect(url_for('admin_portal'))
        else:
            return render_template('addproperty.html')
    else:
        return redirect(url_for('login'))


@app.route("/updateproperty/<propertyID>", methods=["GET", "POST"])
def update_property(propertyID):
    if session.get('loggedin'):
        if request.method == "POST":
            propSize = request.form.get('propertySize')
            propType = request.form.get('propertyType')
            numBeds = request.form.get('numBeds')
            numBaths = request.form.get('numBaths')
            address = request.form.get('address')
            if propType:
                db_insert(f'UPDATE Property SET type = "{propType}" WHERE propertyID = {propertyID}')
            if propSize:
                db_insert(f'UPDATE Property SET size = "{propSize}" WHERE propertyID = {propertyID}')
            if numBeds:
                db_insert(f'UPDATE Property SET numBeds = {numBeds} WHERE propertyID = {propertyID}')
            if numBaths:
                db_insert(f'UPDATE Property SET numBaths = {numBaths} WHERE propertyID = {propertyID}')
            if address:
                db_insert(f'UPDATE Property SET address = "{address}" WHERE propertyID = {propertyID}')
            return redirect(url_for('admin_portal'))
        else:
            return render_template('updateproperty.html', prop_id=propertyID)
    else:
        return redirect(url_for('login'))


@app.route("/property/<propertyID>", methods=["GET", "POST"])
def view_property(propertyID):
    if session.get('loggedin'):
        data_dict = get_property_info(propertyID)
        # TODO: sometimes images get saved multiple times, fix
        # update: the images get saved again if the user refreshes this page
        if request.method == "POST":
            files = request.files.getlist("files")
            for i, file in enumerate(files):
                path = os.path.join(app.config['UPLOAD_FOLDER'], str(session['agentID']), "PROPERTY", propertyID, f"{propertyID}-{i}-{datetime.datetime.now().year + datetime.datetime.now().day + datetime.datetime.now().hour + datetime.datetime.now().second}.png")
                if allowed_file(file.filename):
                    file.save(path)
                else:
                    print("Error: file type not accepted")
        img_list = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], str(session['agentID']), "PROPERTY", propertyID))
        # it works ¯\_(ツ)_/¯
        return render_template('viewproperty.html', items=tuple(data_dict.items()), prop_id=int(propertyID), prop=propertyID, filelist=img_list, agent=str(session['agentID']))
    else:
        return redirect(url_for('login'))


@app.route("/showcase/<propertyID>", methods=["GET", "POST"])
def showcase_property(propertyID):
    if session.get('loggedin'):
        data_dict = get_property_info(propertyID)
        img_list = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], str(session['agentID']), "PROPERTY", propertyID))
        return render_template('showcase.html', items=tuple(data_dict.items()), prop_id=int(propertyID), prop=propertyID, filelist=img_list, agent=str(session['agentID']))
    else:
        return redirect(url_for('login'))


@app.route("/signin/<propertyID>", methods=["GET", "POST"])
def guest_signin(propertyID):
    if not session.get('loggedin'):
        return render_template('login.html')

    if request.method == "POST":
        data_dict = get_property_info(propertyID)
        img_list = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], str(session['agentID']), "PROPERTY", propertyID))
        guest_fname = request.form.get('guestFName')
        guest_lname = request.form.get('guestLName')
        prop_id_guest = int(propertyID)
        curr_date = datetime.datetime.today()
        guest_email = request.form.get('guestEmail')
        if guest_email:
            db_insert(f'INSERT INTO Guest (propertyID, guestFName, guestLName, guestEmail, dateOfVisit) VALUES ({prop_id_guest}, "{guest_fname}", "{guest_lname}", "{guest_email}", "{curr_date}")')
        else:
            db_insert( f'INSERT INTO Guest (propertyID, guestFName, guestLName, dateOfVisit) VALUES ({prop_id_guest}, "{guest_fname}", "{guest_lname}", "{curr_date}")')
        # print(db_select(f'SELECT * FROM Guest'))
        return render_template('showcase.html', items=tuple(data_dict.items()), prop_id=int(propertyID), prop=propertyID, filelist=img_list, agent=str(session['agentID']))
    else:
        return render_template('guestsignin.html', prop_id=propertyID)


@app.route("/viewguests")
def view_guests():
    properties = db_select(f"SELECT propertyID, address FROM Property WHERE agentID = {session['agentID']}")
    guests = {}
    for prop in properties:
        guest_info = db_select(f"SELECT * FROM Guest WHERE propertyID = {prop[0]}")
        guests[prop[1]] = [guest_info]
    return guests


def db_select(query) -> list:
    bt = sqlite3.connect("boomtown.db")
    cur = bt.cursor()
    data = cur.execute(query).fetchall()
    cur.close()
    return data


def db_insert(query):
    bt = sqlite3.connect("boomtown.db")
    cur = bt.cursor()
    cur.execute(query)
    bt.commit()
    cur.close()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def gen_safe_password(plaintext):
    bytes = plaintext.encode("utf-8")
    return bcrypt.hashpw(bytes, SALT)


def get_property_info(prop_id) -> dict:
    propertyID = prop_id[0]
    prop_data = db_select(f'SELECT * FROM Property WHERE propertyID = {propertyID}')[0]
    data_dict = {
        "Property ID": int(propertyID),
        "Agent ID": prop_data[1],
        "Property Type": prop_data[2],
        "Property Size": prop_data[3],
        "Number of Bedrooms": prop_data[4],
        "Number of Bathrooms": prop_data[5],
        "Address of Property": prop_data[6]
    }
    return data_dict


if __name__ == "__main__":
    app.run()
