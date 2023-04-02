from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
import os

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'media')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = 'qm$Fx%tvPpGi?k+/32iiRL-v??o)wJLtE@1/Z$u-%)#4ia~sc'

# initial database stuff
# TODO: add to separate function to reduce code duplication
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
        password = request.form['password']
        account = db_select(f'SELECT * FROM Agent WHERE email = "{email}" AND password = "{password}"')[0]
        if account:
            session['loggedin'] = True
            session['email'] = email
            session['fname'] = account[1]
            session['lname'] = account[2]
            session['phone'] = account[5]
            session['agentID'] = account[0]
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
        password = request.form['password']
        fname = request.form['agentFName']
        lname = request.form['agentLName']
        phone = request.form['phone']
        account = db_select(f'SELECT * FROM Agent WHERE email = "{email}"')
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address'
        elif not fname or not lname or not phone or not password or not email:
            msg = 'Please fill out the form'
        else:
            session['loggedin'] = True
            session['email'] = email
            session['fname'] = fname
            session['lname'] = lname
            session['phone'] = phone
            db_insert(f'INSERT INTO Agent (agentFName, agentLName, email, password, phone) VALUES ("{fname}", "{lname}", "{email}", "{password}", "{phone}")')
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


@app.route("/portal")
def admin_portal():
    if session.get('loggedin'):
        prop_list = db_select(f"SELECT * FROM Property WHERE agentID = {session['agentID']}")
        return render_template('index.html', user_image=os.path.join(app.config['UPLOAD_FOLDER'], "1", "AGENT", 'default.png'), list=prop_list)
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


# TODO: add a button to allow user to upload pictures. Display all pictures
@app.route("/property/<propertyID>", methods=["GET", "POST"])
def view_property(propertyID):
    if session.get('loggedin'):
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
        return render_template('viewproperty.html', dict_size=len(data_dict), items=tuple(data_dict.items()), prop_id=int(propertyID))
    else:
        return redirect(url_for('login'))


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


if __name__ == "__main__":
    app.run()
