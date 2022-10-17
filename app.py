from flask import Flask, render_template, url_for, session, request, redirect
import requests
import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth, firestore

app = Flask(__name__)

#initialize firebase
cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbconfig.json')))
db = firestore.client()

#Initialze person as dictionary
person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}

@app.route('/')

@app.route('/login', methods=['POST', 'GET'])
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register_page():
    return render_template('register.html')

@app.route('/login_user', methods=['POST', 'GET'])
def login_user():
    if request.method == 'POST':
        result = request.form
        email = result.get('email')
        password = result.get('password')
        try:
            user = pb.auth().sign_in_with_email_and_password(email, password)
            #Insert the user data in the global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            #Get the name of the user
            data = db.collection("users").document(person["uid"]).get().to_dict()
            person["name"] = data["name"]
            #Redirect to home page
            return redirect(url_for('home_page'))
        except:
            return redirect(url_for('login_page'))

@app.route('/register_user', methods=['POST', 'GET'])
def register_user():
    if request.method == 'POST':
        result = request.form
        email = result.get('email')
        password = result.get('password')
        name = result.get('name')
        dob = result.get('DOB')
        gender = result.get('gender')
        try:
            #Try creating the user account using the provided data
            auth.create_user(email=email, password=password)
            user = pb.auth().sign_in_with_email_and_password(email, password)
            print(user)
            #Add data to global person
            global person
            person["is_logged_in"] = True
            person["email"] = email
            person["uid"] = user['localId']
            person["name"] = name
            person['DOB'] = dob
            person['gender'] = gender
            print("hi")
            pb.auth().send_email_verification(user['idToken'])
            print("hi")
            #Append data to the firebase realtime database
            data = {"name": name, "email": email, "password": password, 'dob': dob, "gender": gender}
            db.collection("users").document(person["uid"]).set(data)
            #Go to home page
            return redirect(url_for('home_page'))
        # if the email is registered, redirect to the login page
        except firebase_admin._auth_utils.EmailAlreadyExistsError as e:
            return redirect(url_for('login_page'))
        except Exception as e:
            print(e)
            return redirect(url_for('register_page'))

@app.route('/home')
def home_page():
    if person["is_logged_in"] == True:
        return render_template("home.html", name = person["name"])
    else:
        return redirect(url_for('login'))


@app.route('/diagnosis')
def diagnosis_page():
    return render_template('diagnosis.html')


@app.route('/simulation')
def simulation_page():
    return render_template('simulation.html')


@app.route('/report')
def report_page():
    return render_template('report.html')

@app.route('/report_detail')
def report_detail_page():
    return render_template('report_detail.html')

@app.route('/appointment')
def appointment_page():
    return render_template('appointment.html')


@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/contact')
def contact_page():
    return render_template('contact.html')


@app.route('/profile')
def profile_page():
    return render_template('profile.html')



if __name__ == '__main__':
    app.run()


