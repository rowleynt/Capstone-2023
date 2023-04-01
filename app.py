from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
import os

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'media')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        password = request.form['password']
        db = sqlite3.connect("boomtown.db")
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM Agent WHERE email = "{email}" AND password = "{password}"')
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['email'] = email
            session['fname'] = account[1]
            session['lname'] = account[2]
            session['phone'] = account[5]
            session['agentID'] = account[0]
            msg = 'Logged in successfully'
            # return render_template('index.html', msg=msg, user_image=os.path.join(app.config['UPLOAD_FOLDER'], 'real.jpg'))
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


# TODO: when making folders, add 'AGENT' and 'PROPERTY' inside of agent folder
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'agentFName' in request.form and 'agentLName' in request.form and 'email' in request.form and 'password' in request.form and 'email' in request.form and 'phone' in request.form:
        email = request.form['email']
        password = request.form['password']
        fname = request.form['agentFName']
        lname = request.form['agentLName']
        phone = request.form['phone']
        db = sqlite3.connect("boomtown.db")
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM Agent WHERE email = "{email}"')
        account = cursor.fetchone()
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
            cursor.execute(f'INSERT INTO Agent (agentFName, agentLName, email, password, phone) VALUES ("{fname}", "{lname}", "{email}", "{password}", "{phone}")')
            db.commit()
            aID = cursor.execute(f'SELECT agentID FROM Agent WHERE email = "{email}"').fetchone()
            session['agentID'] = aID[0]
            msg = 'Logged in successfully'
            # return render_template('index.html', msg=msg, user_image=os.path.join(app.config['UPLOAD_FOLDER'], 'real.jpg'))
            return redirect(url_for('admin_portal'))
    elif request.method == 'POST':
        msg = 'Please fill out the form'
    return render_template('register.html', msg=msg)


@app.route("/portal")
def admin_portal():
    if session.get('loggedin'):
        conn = sqlite3.connect("boomtown.db")
        proplist = list(conn.execute(f"SELECT * FROM Property WHERE agentID = {session['agentID']}").fetchall())
        return render_template('index.html', user_image=os.path.join(app.config['UPLOAD_FOLDER'], 'real.jpg'), list=proplist)
    else:
        return redirect(url_for('login'))


# TODO: get current property ID and make folder in agent 'PROPERTY' folder with property id
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

            db = sqlite3.connect("boomtown.db")
            conn = db.cursor()
            conn.execute(f'INSERT INTO Property (agentID, type, size, numBeds, numBaths, address) VALUES ({currAgent}, "{propSize}", "{propType}", {numBeds}, {numBaths}, "{address}")')
            db.commit()
            conn.close()

            # print(propType, propSize, numBaths, numBeds, address, currAgent)
            return redirect(url_for('admin_portal'))
        else:
            return render_template('addproperty.html')
    else:
        return redirect(url_for('login'))


# TODO: display property information on page, add a button to allow user to edit information and upload pictures. Display all pictures
@app.route("/viewproperty/<propertyID>", methods=["GET", "POST"])
def view_property(propertyID):
    return f"propertyID: {propertyID}"


if __name__ == "__main__":
    app.run()
