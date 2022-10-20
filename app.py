import time
import datetime
from datetime import date,timedelta

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
person = {"is_logged_in": False, "username": "", "fname": "", "lname": "", "email": "", "uid": "", "gender": "", "dob": ""}

#initalize report_id for diagnosis
diagnosis_report = {}
report_id = ""

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
            person["email"] = email
            person["uid"] = user['localId']
            #Get the name of the user
            data = db.collection("users").document(person["uid"]).get().to_dict()
            print(data)
            print(person)
            person["username"] = data["username"]
            person["fname"] = data["fname"]
            person["lname"] = data["lname"]
            person['dob'] = data["dob"]
            person['gender'] = data["gender"]
            #Redirect to home page
            return redirect(url_for('home_page'))
        except Exception as e:
            print(e)
            return redirect(url_for('login_page'))

@app.route('/register_user', methods=['POST', 'GET'])
def register_user():
    if request.method == 'POST':
        result = request.form
        email = result.get('email')
        password = result.get('password')
        fname = result.get('fname')
        lname = result.get('lname')
        username = result.get('username')
        dob = result.get('dob')
        gender = result.get('gender')
        print(dob)
        try:
            #Try creating the user account using the provided data
            auth.create_user(email=email, password=password)
            user = pb.auth().sign_in_with_email_and_password(email, password)
            #Add data to global person
            global person
            person["is_logged_in"] = True
            person["email"] = email
            person["uid"] = user['localId']
            person["fname"] = fname
            person["lname"] = lname
            person["username"] = username
            person['dob'] = dob
            person['gender'] = gender
            print("hi")
            pb.auth().send_email_verification(user['idToken'])
            print("hi")
            #Append data to the firebase realtime database
            data = {"fname": fname, "lname": lname, "username": username, "email": email, "password": password, 'dob': dob, "gender": gender}
            print(data)
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
        return render_template("home.html", name = person["username"])
    else:
        return redirect(url_for('login'))


@app.route('/diagnosis', methods=['POST', 'GET'])
def diagnosis_page():
    return render_template('diagnosis.html')


@app.route('/diagnosis_user', methods=['POST', 'GET'])
def diagnosis_user():
    error = None
    if request.method == 'POST':
        result = request.form
        #get basic information
        sex = float(result.get('sex'))
        age = float(result.get('age'))
        HE_ht = float(result.get('HE_ht'))
        HE_wt = float(result.get('HE_wt'))
        HE_wc = float(result.get('HE_wc'))
        #calculate BMI
        HE_BMI = HE_wt / (HE_ht / 100) ** 2
        #pre-processing for obesity
        if HE_BMI <= 18.5:
            HE_obe = 1
        elif HE_BMI <= 25:
            HE_obe = 2
        else:
            HE_obe = 3

        #Get blood test reusults
        bloodtest = float(result.get('bloodtest'))
        if bloodtest == 1:
            HE_sbp = float(result.get('HE_sbp'))
            HE_dbp = float(result.get('HE_dbp'))
            HE_chol = float(result.get('HE_chol'))
            HE_HDL_st2 = float(result.get('HE_HDL_st2'))
            HE_TG = float(result.get('HE_TG'))
            HE_glu = float(result.get('HE_glu'))
            HE_HbA1c = float(result.get('HE_HbA1c'))
            HE_BUN = float(result.get('HE_BUN'))
            HE_crea = float(result.get('HE_crea'))
        else:
            HE_sbp = None
            HE_dbp = None
            HE_chol = None
            HE_HDL_st2 = None
            HE_TG = None
            HE_glu = None
            HE_HbA1c = None
            HE_BUN = None
            HE_crea = None

        #get lifestyles
        dr_month = float(result.get('dr_month'))
        dr_high = float(result.get('dr_high'))
        sm_presnt = float(result.get('sm_presnt'))
        mh_stress = float(result.get('mh_stress'))
        pa_vig_tm = float(result.get('pa_vig_tm'))
        pa_mod_tm = float(result.get('pa_mod_tm'))
        pa_walk = float(result.get('pa_walk'))
        pa_aerobic = float(result.get('pa_aerobic'))

        #get history disease
        DI3_dg = float(result.get('DI3_dg'))
        DI4_dg = float(result.get('DI4_dg'))
        HE_DMfh = float(result.get('HE_DMfh'))
        DE1_3 = float(result.get('DE1_3'))
        DE1_31 = result.get('DE1_31')
        if DE1_31 is not None:
            DE1_31 = float(DE1_31)
        else:
            DE1_31 = None

        DE1_32 = result.get('DE1_32')
        if DE1_32 is not None:
            DE1_32 = float(DE1_32)
        else:
            DE1_32 = None

        print(result.to_dict())
        try:
            # Get the name of the user
            past_report_ref = db.collection("users").document(person["uid"]).collection('past_reports').document()
            global diagnosis_report
            diagnosis_report = { "diagnosis_time": datetime.datetime.now(tz=datetime.timezone.utc), "sex": sex, "age": age, "HE_ht": HE_ht, "HE_wt": HE_wt, "HE_wc": HE_wc, "HE_BMI": HE_BMI, "HE_obe": HE_obe,
                                "bloodtest": bloodtest, "HE_sbp": HE_sbp, "HE_dbp": HE_dbp, "HE_chol": HE_chol, "HE_HDL_st2": HE_HDL_st2, "HE_TG": HE_TG,
                                "HE_glu": HE_glu, "HE_HbA1c": HE_HbA1c, "HE_BUN": HE_BUN, "HE_crea": HE_crea,
                                "dr_month": dr_month, "dr_high": dr_high, "sm_presnt": sm_presnt, "mh_stress": mh_stress, "pa_vig_tm": pa_vig_tm,
                                "pa_mod_tm": pa_mod_tm, "pa_walk": pa_walk, "pa_aerobic": pa_aerobic,
                                "DI3_dg": DI3_dg, "DI4_dg": DI4_dg, "HE_DMfh": HE_DMfh, "DE1_3": DE1_3, "DE1_31": DE1_31, "DE1_32": DE1_32}
            past_report_ref.set(diagnosis_report)
            global report_id
            report_id = past_report_ref.id
            print(report_id)
            print(diagnosis_report)
            return render_template('report_detail.html')
        except Exception as e:
            print(e)
            return render_template('diagnosis.html')





@app.route('/simulation')
def simulation_page():
    return render_template('simulation.html')


@app.route('/report')
def report_page():
    past_reports = db.collection("users").document(person["uid"]).collection("past_reports").stream()
    report_list_random = []
    for report in past_reports:
        report_list_random.append(report.to_dict())
        print(f'{report.id} => {report.to_dict()}')
    print(report_list_random)
    report_list_sorted = sorted(report_list_random, key=lambda x: x.get('diagnosis_time'))
    length = len(report_list_sorted)
    return render_template('report.html', past_reports = report_list_sorted, length = length)
    

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
    return render_template('profile.html', username = person["username"], fname = person["fname"], lname = person["lname"], email = person["email"], gender = person["gender"], dob = person["dob"])

@app.route('/change_username')
def change_username():
    if request.method == 'POST':
        result = request.form
        username = result.get('username')
        try: 
            #change username to the firebase realtime database
            data = {"username": username}
            db.collection("users").document(person["uid"]).update(data)
            return redirect(url_for('profile_page'))
        except Exception as e:
            print(e)
            return redirect(url_for('profile_page'))
    

@app.route('/delete_account')
def delete_account():
    try: 
        user = auth.get_user_by_email(person['email'])
        auth.delete_user(user.uid)
        db.collection("users").document(person["uid"]).delete()
        return redirect(url_for('login_page'))
    except Exception as e:
        print(e)
        return redirect(url_for('profile_page'))

        

if __name__ == '__main__':
    app.run()


