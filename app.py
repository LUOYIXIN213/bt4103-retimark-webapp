import time
import datetime
from datetime import date,timedelta
from forms import RegistrationForm, LoginForm

from flask import Flask, render_template, url_for, session, request, redirect
import requests
import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth, firestore
import numpy as np
import pickle
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
import sklearn
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba240'

#initialize firebase
cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbconfig.json')))
db = firestore.client()

#Initialze person as dictionary
person = {"is_logged_in": False, "username": "", "fullname": "", "email": "", "uid": "", "dob": "", "risk_score_goal": ""}

#initalize report_id for diagnosis
diagnosis_report = {}
report_id = ""

#initialze id for simulation
simulation_report = {}
simulation_id = ""

#load machine learning model
model = pickle.load(open("finalized_model.pkl", 'rb'))



@app.route('/')

@app.route('/login', methods=['POST', 'GET'])
def login_page():
    form = LoginForm()
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['POST', 'GET'])
def register_page():
    form = RegistrationForm()
    return render_template('register.html', title='Register', form=form)

@app.route('/login_user', methods=['POST', 'GET'])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
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
                person["username"] = data["username"]
                person["fullname"] = data["fullname"]
                person['dob'] = data["dob"]
                person["risk_score_goal"] = data["risk_score_goal"]
                #Redirect to home page
                return redirect(url_for('home_page'))
            except Exception as e:
                print(e)
                return redirect(url_for('login_page'))
    else:
        return render_template('login.html', title='Login', form=form)

@app.route('/register_user', methods=['POST', 'GET'])
def register_user():
    form = RegistrationForm()
    if form.validate_on_submit():
        if request.method == 'POST':
            result = request.form
            email = result.get('email')
            password = result.get('password')
            fullname = result.get('fullname')
            username = result.get('username')
            dob = result.get('birthday')
            try:
                #Try creating the user account using the provided data
                auth.create_user(email=email, password=password)
                user = pb.auth().sign_in_with_email_and_password(email, password)
                #Add data to global person
                global person
                person["is_logged_in"] = True
                person["email"] = email
                person["uid"] = user['localId']
                person["fullname"] = fullname
                person["username"] = username
                person['dob'] = dob
                person["risk_score_goal"] = 40
                pb.auth().send_email_verification(user['idToken'])
                #Append data to the firebase realtime database
                data = {"fullname": fullname, "username": username, "email": email, "password": password, 'dob': dob, "risk_score_goal":40}
                db.collection("users").document(person["uid"]).set(data)
                #Go to home page
                return redirect(url_for('home_page'))
            # if the email is registered, redirect to the login page
            except firebase_admin._auth_utils.EmailAlreadyExistsError as e:
                return redirect(url_for('login_page'))
            except Exception as e:
                print(e)
                return redirect(url_for('register_page'))
    return render_template('register.html', title='Register', form=form)
    


@app.route('/home')
def home_page():
    if person["is_logged_in"] == True:
        data = db.collection("users").document(person["uid"]).get().to_dict()
        risk_score_goal = data['risk_score_goal']
        past_reports_ref = db.collection("users").document(person["uid"]).collection("past_reports")
        query = past_reports_ref.order_by("diagnosis_time", direction=firestore.Query.DESCENDING).limit(5)
        results = query.stream()
        report_list = []
        latest_report = []
        second_latest_report = []
        third_latest_report = []
        fourth_latest_report = []
        fifth_latest_report = []
        latest_diagnosis_date = ''
        second_diagnosis_date = ''
        third_diagnosis_date = ''
        fourth_diagnosis_date = ''
        fifth_diagnosis_date = ''
        for doc in results:
            report_list.append(doc.to_dict())
        if len(report_list) != 0:
            latest_report = report_list[0]
            date_time_str = latest_report['diagnosis_time'] + timedelta(hours=8)
            latest_diagnosis_date = date_time_str.strftime("%Y-%m-%d %H:%M")
            #print(report_list[0])
            #print(len(report_list))
            if len(report_list) >= 2:
                #print(report_list[1])
                second_latest_report = report_list[1]
                second_date_time_str = second_latest_report['diagnosis_time'] + timedelta(hours=8)
                second_diagnosis_date = second_date_time_str.strftime("%Y-%m-%d %H:%M")
                if len(report_list) >= 3:
                    #print(report_list[2])
                    third_latest_report = report_list[2]
                    third_date_time_str = third_latest_report['diagnosis_time'] + timedelta(hours=8)
                    third_diagnosis_date = third_date_time_str.strftime("%Y-%m-%d %H:%M")
                    if len(report_list) >= 4:
                        #print(report_list[2])
                        fourth_latest_report = report_list[3]
                        fourth_date_time_str = fourth_latest_report['diagnosis_time'] + timedelta(hours=8)
                        fourth_diagnosis_date = fourth_date_time_str.strftime("%Y-%m-%d %H:%M")
                        if len(report_list) == 5:
                            #print(report_list[2])
                            fifth_latest_report = report_list[4]
                            fifth_date_time_str = fifth_latest_report['diagnosis_time'] + timedelta(hours=8)
                            fifth_diagnosis_date = fifth_date_time_str.strftime("%Y-%m-%d %H:%M")
                        else:
                            fifth_diagnosis_date = "NA"
                    else:
                        fourth_diagnosis_date = "NA"
                        fifth_diagnosis_date = "NA"
                else:
                    third_diagnosis_date = "NA"
                    fourth_diagnosis_date = "NA"
                    fifth_diagnosis_date = "NA"
            else:
                second_diagnosis_date = "NA"
                third_diagnosis_date = "NA"
                fourth_diagnosis_date = "NA"
                fifth_diagnosis_date = "NA"
        else:
            latest_diagnosis_date = 'NA'
            second_diagnosis_date = "NA"
            third_diagnosis_date = "NA"
            fourth_diagnosis_date = "NA"
            fifth_diagnosis_date = "NA"
            latest_report = {"risk_score": "not diagnosed yet"}
        return render_template("home.html", risk_score_goal = int(risk_score_goal), name = person["username"], latest_report=latest_report,
                               latest_diagnosis_date=latest_diagnosis_date, second_latest_report=second_latest_report,
                               second_diagnosis_date=second_diagnosis_date, third_latest_report=third_latest_report,
                               third_diagnosis_date=third_diagnosis_date, fourth_latest_report=fourth_latest_report,
                               fourth_diagnosis_date=fourth_diagnosis_date, fifth_latest_report=fifth_latest_report,
                               fifth_diagnosis_date=fifth_diagnosis_date)
    else:
        return redirect(url_for('login'))


@app.route('/diagnosis', methods=['POST', 'GET'])
def diagnosis_page():
    if person["is_logged_in"] == True:
        latest_report = []
        diagnosis_str = ''
        past_reports_ref = db.collection("users").document(person["uid"]).collection("past_reports")
        query = past_reports_ref.order_by("diagnosis_time", direction=firestore.Query.DESCENDING).limit(1)
        results = query.stream()
        report_list = []
        for doc in results:
            report_list.append(doc.to_dict())
        if len(report_list) != 0:
            latest_report = report_list[0]
            date_time_str = latest_report['diagnosis_time'] + timedelta(hours=8)
            diagnosis_str = date_time_str.strftime("%Y-%m-%d %H:%M:%S")
            print(report_list[0])
        return render_template('diagnosis.html', latest_report=latest_report,
                               diagnosis_date= diagnosis_str)
    else:
        return redirect(url_for('login'))


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
        N_PROT = float(result.get('N_PROT'))
        N_FAT = float(result.get('N_FAT'))
        N_CHO = float(result.get('N_CHO'))
        dr_month = float(result.get('dr_month'))
        dr_high = float(result.get('dr_high'))
        sm_presnt = float(result.get('sm_presnt'))
        mh_stress = float(result.get('mh_stress'))
        pa_vig_tm = float(result.get('pa_vig_tm'))
        pa_mod_tm = float(result.get('pa_mod_tm'))
        pa_walkMET = float(result.get('pa_walkMET')) * 3.3
        pa_aerobic = float(result.get('pa_aerobic'))

        #preprocess for physical activity
        pa_vigMET = 8 * pa_vig_tm
        pa_modMET = 4 * pa_mod_tm
        pa_totMET = pa_walkMET + pa_modMET + pa_vigMET

        #get history disease
        DI3_dg = float(result.get('DI3_dg'))
        DI4_dg = float(result.get('DI4_dg'))
        HE_DMfh = float(result.get('HE_DMfh'))
        DE1_3 = float(result.get('DE1_3'))
        DI1_2 = float(result.get('DI1_2'))
        DI2_2 = float(result.get('DI2_2'))
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

        #preproccessing for HE_HP
        HE_HP = None
        if bloodtest == 1:
            if 0< HE_sbp < 120 and 0 < HE_dbp < 80:
                HE_HP = 1
            elif 120 <= HE_sbp < 140 or 80 <= HE_dbp < 90:
                HE_HP = 2
            elif 140 <= HE_sbp or 90 <= HE_dbp or DI1_2 == 1:
                HE_HP = 3
            else:
                HE_HP = None
        elif DI1_2 == 1:
            HE_HP = 3
        else:
            HE_HP = None

        #preprocessing for HE_HCHOL
        HE_HCHOL = 0
        if bloodtest == 1:
            if HE_chol >= 240 or DI2_2 == 1:
                HE_HCHO = 1
        elif DI2_2 == 1:
            HE_HCHOL = 0
        else:
            HE_HCHOL = 0

        #preprocessign for HE_HTG
        HE_HTG = 0
        if bloodtest == 1:
            if HE_TG >= 200:
                HE_HTG = 1
        else:
            HE_HTG = 0

        print(result.to_dict())
        try:
            # Get the name of the user
            past_report_ref = db.collection("users").document(person["uid"]).collection('past_reports').document()
            global diagnosis_report

            #Run machine learning model to generate risk score
            # 23 independent variables to input in the model
            #['pa_totMET', 'N_PROT', 'N_CHO', 'N_FAT', 'HE_wc', 'HE_BMI',
            # 'HE_sbp', 'HE_dbp', 'HE_HbA1c', 'HE_BUN', 'HE_crea', 'HE_HDL_st2',
            # 'HE_TG', 'age', 'DI3_dg', 'DI4_dg', 'HE_DMfh', 'sm_presnt',
            # 'HE_obe', 'HE_HP', 'HE_HCHOL', 'HE_HTG', 'sex']

            #risk score prediction for with blood test
            rounded_risk_score = None
            risk_score_glucose_25 = None
            risk_score_glucose_50 = None
            risk_score_glucose_75 = None
            risk_score_glucose_100 = None

            #predicted diabetes class
            predicted_class = None
            predicted_class_glucose_25 = None
            predicted_class_glucose_50 = None
            predicted_class_glucose_75 = None
            predicted_class_glucose_100 = None

            if bloodtest == 1:
                t = pd.DataFrame(np.array(
                    [pa_totMET, HE_wc, HE_BMI, N_PROT, N_CHO, N_FAT, HE_sbp, HE_dbp, HE_HbA1c, HE_BUN, HE_crea,
                     HE_HDL_st2, HE_TG, age, DI3_dg, DI4_dg, HE_DMfh, HE_obe, HE_HP, HE_HCHOL,
                     HE_HTG, sm_presnt, sex]).reshape(-1, 23), columns=['pa_totMET','HE_wc', 'HE_BMI', 'N_PROT', 'N_CHO',
                                                                        'N_FAT', 'HE_sbp',
                                                                        'HE_dbp', 'HE_HbA1c', 'HE_BUN', 'HE_crea', 'HE_HDL_st2',
                                                                        'HE_TG', 'age', 'DI3_dg', 'DI4_dg', 'HE_DMfh', 'HE_obe',
                                                                        'HE_HP', 'HE_HCHOL', 'HE_HTG', 'sm_presnt', 'sex'])
                diagnosed_class = model.predict(t)
                predicted_class = float(diagnosed_class[0])
                risk_score = model.predict_proba(t)[0][1]
                rounded_risk_score = float(round(risk_score*100))
                print(predicted_class)
                print(rounded_risk_score)

            #risk score prediction for without blood test in confidence interval
            else:
                #generate risk score if HE_glu being in the 0 th percentile to 25 th percentile
                t_25 = pd.DataFrame(np.array(
                    [pa_totMET, HE_wc, HE_BMI, N_PROT, N_CHO, N_FAT, 117.41880341880342, 74.85919928025191,
                     5.491408007197482, 15.269005847953217, 0.7982501124606389, 52.62156937907271, 115.519118308592,
                     age, DI3_dg, DI4_dg, HE_DMfh, HE_obe, 1.0, 0,
                     0, sm_presnt, sex]).reshape(-1, 23), columns=['pa_totMET','HE_wc', 'HE_BMI', 'N_PROT', 'N_CHO',
                                                                        'N_FAT', 'HE_sbp',
                                                                        'HE_dbp', 'HE_HbA1c', 'HE_BUN', 'HE_crea', 'HE_HDL_st2',
                                                                        'HE_TG', 'age', 'DI3_dg', 'DI4_dg', 'HE_DMfh', 'HE_obe',
                                                                        'HE_HP', 'HE_HCHOL', 'HE_HTG', 'sm_presnt', 'sex'])

                diagnosed_class_25 = model.predict(t_25)
                predicted_class_glucose_25 = float(diagnosed_class_25[0])
                risk_score_25 = model.predict_proba(t_25)[0][1]
                risk_score_glucose_25 = float(round(risk_score_25*100))
                print(predicted_class_glucose_25)
                print(risk_score_glucose_25)

                #generate risk score if HE_glu being in the 25 th percentile to 50 th percentile
                t_50 = pd.DataFrame(np.array(
                    [pa_totMET, HE_wc, HE_BMI, N_PROT, N_CHO, N_FAT, 120.78805194805194, 76.36675324675325,
                     5.584675324675325, 15.613506493506494, 0.8022701298701298, 50.89999223103178, 129.25194805194806,
                     age, DI3_dg, DI4_dg, HE_DMfh, HE_obe, 1, 0,
                     0, sm_presnt, sex]).reshape(-1, 23), columns=['pa_totMET','HE_wc', 'HE_BMI', 'N_PROT', 'N_CHO',
                                                                        'N_FAT', 'HE_sbp',
                                                                        'HE_dbp', 'HE_HbA1c', 'HE_BUN', 'HE_crea', 'HE_HDL_st2',
                                                                        'HE_TG', 'age', 'DI3_dg', 'DI4_dg', 'HE_DMfh', 'HE_obe',
                                                                        'HE_HP', 'HE_HCHOL', 'HE_HTG', 'sm_presnt', 'sex'])

                diagnosed_class_50 = model.predict(t_50)
                predicted_class_glucose_50 = float(diagnosed_class_50[0])
                risk_score_50 = model.predict_proba(t_50)[0][1]
                risk_score_glucose_50 = float(round(risk_score_50*100))
                print(predicted_class_glucose_50)
                print(risk_score_glucose_50)

                #generate risk score if HE_glu being in the 50 th percentile to 75 th percentile
                t_75 = pd.DataFrame(np.array(
                    [pa_totMET, HE_wc, HE_BMI, N_PROT, N_CHO, N_FAT, 124.16230366492147, 77.2324607329843,
                     5.739895287958115, 16.05759162303665, 0.8326178010471204, 49.74235817995025, 142.69476439790577,
                     age, DI3_dg, DI4_dg, HE_DMfh, HE_obe, 3, 0,
                     0, sm_presnt, sex]).reshape(-1, 23), columns=['pa_totMET','HE_wc', 'HE_BMI', 'N_PROT', 'N_CHO',
                                                                        'N_FAT', 'HE_sbp',
                                                                        'HE_dbp', 'HE_HbA1c', 'HE_BUN', 'HE_crea', 'HE_HDL_st2',
                                                                        'HE_TG', 'age', 'DI3_dg', 'DI4_dg', 'HE_DMfh', 'HE_obe',
                                                                        'HE_HP', 'HE_HCHOL', 'HE_HTG', 'sm_presnt', 'sex'])

                diagnosed_class_75 = model.predict(t_75)
                predicted_class_glucose_75 = float(diagnosed_class_75[0])
                risk_score_75 = model.predict_proba(t_75)[0][1]
                risk_score_glucose_75 = float(round(risk_score_75*100))
                print(predicted_class_glucose_75)
                print(risk_score_glucose_75)

                #generate risk score if HE_glu being in the 75 th percentile to 100th percentile
                t_100 = pd.DataFrame(np.array(
                    [pa_totMET, HE_wc, HE_BMI, N_PROT, N_CHO, N_FAT, 126.92238648363252, 77.0063357972545,
                     6.763727560718057, 16.50897571277719, 0.8618532206969378, 46.931693880777516, 172.6441393875396,
                     age, DI3_dg, DI4_dg, HE_DMfh, HE_obe, 3, 0,
                     0, sm_presnt, sex]).reshape(-1, 23), columns=['pa_totMET','HE_wc', 'HE_BMI', 'N_PROT', 'N_CHO',
                                                                        'N_FAT', 'HE_sbp',
                                                                        'HE_dbp', 'HE_HbA1c', 'HE_BUN', 'HE_crea', 'HE_HDL_st2',
                                                                        'HE_TG', 'age', 'DI3_dg', 'DI4_dg', 'HE_DMfh', 'HE_obe',
                                                                        'HE_HP', 'HE_HCHOL', 'HE_HTG', 'sm_presnt', 'sex'])

                diagnosed_class_100 = model.predict(t_100)
                predicted_class_glucose_100 = float(diagnosed_class_100[0])
                risk_score_100 = model.predict_proba(t_100)[0][1]
                risk_score_glucose_100 = float(round(risk_score_100*100))
                print(predicted_class_glucose_100)
                print(risk_score_glucose_100)

                rounded_risk_score = round((risk_score_glucose_25 + risk_score_glucose_50 + risk_score_glucose_75 +risk_score_glucose_100) / 4)


            #store all data in dic and upload to database
            diagnosis_report = {"diagnosis_time": datetime.datetime.now(tz=datetime.timezone.utc),
                                "diagnosed_class": predicted_class, "risk_score": rounded_risk_score,
                                "risk_score_glucose_25": risk_score_glucose_25, "predicted_class_glucose_25": predicted_class_glucose_25,
                                "risk_score_glucose_50": risk_score_glucose_50, "predicted_class_glucose_50": predicted_class_glucose_50,
                                "risk_score_glucose_75": risk_score_glucose_75, "predicted_class_glucose_75": predicted_class_glucose_75,
                                "risk_score_glucose_100": risk_score_glucose_100,
                                "predicted_class_glucose_100": predicted_class_glucose_100,
                                "sex": sex, "age": age, "HE_ht": HE_ht, "HE_wt": HE_wt, "HE_wc": HE_wc, "HE_BMI": HE_BMI, "HE_obe": HE_obe,
                                "bloodtest": bloodtest, "HE_sbp": HE_sbp, "HE_dbp": HE_dbp, "HE_chol": HE_chol, "HE_HDL_st2": HE_HDL_st2, "HE_TG": HE_TG,
                                "HE_glu": HE_glu, "HE_HbA1c": HE_HbA1c, "HE_BUN": HE_BUN, "HE_crea": HE_crea,
                                "N_PROT": N_PROT, "N_FAT": N_FAT, "N_CHO": N_CHO,
                                "dr_month": dr_month, "dr_high": dr_high, "sm_presnt": sm_presnt, "mh_stress": mh_stress, "pa_vig_tm": pa_vig_tm,
                                "pa_mod_tm": pa_mod_tm, "pa_walkMET": pa_walkMET, "pa_aerobic": pa_aerobic,
                                "pa_vigMET": pa_vigMET, "pa_modMET": pa_modMET, "pa_totMET": pa_totMET,
                                "DI3_dg": DI3_dg, "DI4_dg": DI4_dg, "HE_DMfh": HE_DMfh, "DE1_3": DE1_3, "DI1_2": DI1_2,
                                "DI2_2": DI2_2, "DE1_31": DE1_31, "DE1_32": DE1_32, "HE_HP": HE_HP, "HE_HCHOL": HE_HCHOL, "HE_HTG": HE_HTG}
            past_report_ref.set(diagnosis_report)
            global report_id
            report_id = past_report_ref.id
            print(report_id)
            print(diagnosis_report)
            if 'bloodtest' == 1:
                return render_template('report_detail_BT.html', report = diagnosis_report)
            else :
                return render_template('report_detail_noBT.html', report = diagnosis_report)
        except Exception as e:
            print(e)
            return render_template('diagnosis.html')




@app.route('/simulation', methods=['POST', 'GET'])
def simulation_page():
    latest_report = {}
    diagnosis_str = ''
    past_reports_ref = db.collection("users").document(person["uid"]).collection("past_reports")
    query = past_reports_ref.order_by("diagnosis_time", direction=firestore.Query.DESCENDING).limit(1)
    results = query.stream()
    report_list = []
    for doc in results:
        report_list.append(doc.to_dict())
    latest_report = report_list[0]
    date_time_str = latest_report['diagnosis_time'] + timedelta(hours=8)
    diagnosis_str = date_time_str.strftime("%Y-%m-%d %H:%M:%S")
    print(report_list[0])
    return render_template('simulation.html', latest_report = latest_report, diagnosis_date = diagnosis_str)

@app.route('/simulation_user', methods=['POST', 'GET'])
def simulation_user():
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
        N_PROT = float(result.get('N_PROT'))
        N_FAT = float(result.get('N_FAT'))
        N_CHO = float(result.get('N_CHO'))
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
        DI1_2 = float(result.get('DI1_2'))
        DI2_2 = float(result.get('DI2_2'))
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

        # preproccessing for HE_HP
        HE_HP = None
        if bloodtest == 1:
            if 0 < HE_sbp < 120 and 0 < HE_dbp < 80:
                HE_HP = 1
            elif 120 <= HE_sbp < 140 or 80 <= HE_dbp < 90:
                HE_HP = 2
            elif 140 <= HE_sbp or 90 <= HE_dbp or DI1_2 == 1:
                HE_HP = 3
            else:
                HE_HP = None
        elif DI1_2 == 1:
            HE_HP = 3
        else:
            HE_HP = None

        # preprocessing for HE_HCHOL
        HE_HCHOL = 0
        if bloodtest == 1:
            if HE_chol >= 240 or DI2_2 == 1:
                HE_HCHO = 1
        elif DI2_2 == 1:
            HE_HCHOL = 0
        else:
            HE_HCHOL = 0

        # preprocessign for HE_HTG
        HE_HTG = 0
        if bloodtest == 1:
            if HE_TG >= 200:
                HE_HTG = 1
        else:
            HE_HTG = 0

        print(result.to_dict())
        try:
            # Get the name of the user
            simulation_ref = db.collection("users").document(person["uid"]).collection('past_simulations').document()
            global simulation_report
            simulation_report = {"simulated_time": datetime.datetime.now(tz=datetime.timezone.utc), "sex": sex,
                                 "age": age, "HE_ht": HE_ht, "HE_wt": HE_wt, "HE_wc": HE_wc, "HE_BMI": HE_BMI, "HE_obe": HE_obe,
                                 "bloodtest": bloodtest, "HE_sbp": HE_sbp, "HE_dbp": HE_dbp, "HE_chol": HE_chol,
                                 "HE_HDL_st2": HE_HDL_st2, "HE_TG": HE_TG,
                                 "HE_glu": HE_glu, "HE_HbA1c": HE_HbA1c, "HE_BUN": HE_BUN, "HE_crea": HE_crea,
                                 "N_PROT": N_PROT, "N_FAT": N_FAT, "N_CHO": N_CHO,
                                 "dr_month": dr_month, "dr_high": dr_high, "sm_presnt": sm_presnt, "mh_stress": mh_stress, "pa_vig_tm": pa_vig_tm,
                                 "pa_mod_tm": pa_mod_tm, "pa_walk": pa_walk, "pa_aerobic": pa_aerobic,
                                 "DI3_dg": DI3_dg, "DI4_dg": DI4_dg, "HE_DMfh": HE_DMfh, "DE1_3": DE1_3, "DI1_2": DI1_2,
                                 "DI2_2": DI2_2, "DE1_31": DE1_31, "DE1_32": DE1_32, "HE_HP": HE_HP, "HE_HCHOL": HE_HCHOL, "HE_HTG": HE_HTG}
            simulation_ref.set(simulation_report)
            global simulation_id
            simulation_id = simulation_ref.id
            print(simulation_id)
            print(simulation_report)
            return render_template('simulated_score.html')
        except Exception as e:
            print(e)
            return render_template('simulation.html')


@app.route('/report')
def report_page():
    past_reports_ref = db.collection("users").document(person["uid"]).collection("past_reports")
    query = past_reports_ref.order_by("diagnosis_time", direction=firestore.Query.DESCENDING)
    past_reports = query.stream()
    report_list = []
    for report in past_reports:
        report_list.append(report.to_dict())
        print(f'{report.id} => {report.to_dict()}')
    #print(report_list)
    for report in report_list:
        report['diagnosis_time'] = (report['diagnosis_time'] + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        print(report['diagnosis_time'])
    return render_template('report.html', past_reports = report_list)
    

@app.route('/report_detail', methods=['POST', 'GET'])
def report_detail_page():
    if request.method == 'POST':
        result = request.form
        #print(result.to_dict())
        #store the report time when view the report button is clicked, convert to right format
        report_time = result.get('report_time')
        report_date_time = datetime.datetime.strptime(report_time, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
        #print("desired report time in date fromat: ", report_date_time)
        #get the report values specicfic to the report time
        past_reports = db.collection("users").document(person["uid"]).collection("past_reports").stream()
        report = {}
        for doc in past_reports:
            to_str = doc.get("diagnosis_time").strftime("%Y-%m-%d %H:%M:%S")
            to_date = datetime.datetime.strptime(to_str, '%Y-%m-%d %H:%M:%S')
            #print("each doc time in date fromat: ", to_date)
            if to_date == report_date_time:
                report = doc.to_dict()
        #print(report)
        if report['bloodtest'] == 1:
            print(report['bloodtest'])
            return render_template('report_detail_BT.html', report = report)
        else :
            print(report['bloodtest'])
            return render_template('report_detail_noBT.html', report = report)

#@app.route('/diagnosis_report')
#def diagnosis_report_page():
#    return render_template('report_detail.html', report = diagnosis_report)

#take in an array of selected feature values, ordered by importance (follow order of featureName will do) 
#return top 3 most important features with values exceeding diabetic level
featureValue = [23, 171, 4, 22, 100, 23, 55, 13, 22, 50, 133]
def top_advice(featureValue):
    if len(featureValue) == 11:
        HE_HbA1c_diabetic = 7.248061389337642
        #HE_DMfh_diabetic = 0
        #HE_wc_diabetic = 87.8986268174475
        HE_TG_diabetic = 170.07108239095314
        HE_HP_diabetic = 3.0
        pa_totMET_diabetic = 1533.4665589660744
        HE_HDL_st2_diabetic = 46.02331156378242
        HE_HTG_diabetic = 0
        HE_dbp_diabetic = 74.6373182552504
        #DI3_dg_diabetic = 0
        HE_sbp_diabetic = 126.7011308562197
        #DI4_dg_diabetic = 0
        HE_BUN_diabetic = 17.04604200323102
        sm_presnt_diabetic = 0
        HE_crea_diabetic = 0.8868659127625202 
        diabeticValue = [HE_HbA1c_diabetic, HE_TG_diabetic, HE_HP_diabetic, pa_totMET_diabetic, HE_HDL_st2_diabetic, 
                        HE_HTG_diabetic, HE_dbp_diabetic, HE_sbp_diabetic, HE_BUN_diabetic, sm_presnt_diabetic,HE_crea_diabetic] #ordered by importance
        featureName = ["Hemoglobin_A1c (%)", "Triglycerides (mg/dL)", "Hypertension status",
                       "Total MET (min/week)", "HDL cholesterol (mg/dL)", "Hyper triglycerides status", "Diastolic blood pressure (mmHg)", 
                        "Systolic blood pressure (mmHg)", "Blood urea nitrogen (mg/dL)", "Current smoking status", 
                        "Blood serum creatinine (mg/dL)"] #ordered by importance
        adviceList = ["Reduce Hemoglobin_A1c", "Reduce Triglycerides", "About hypertension"] #same order
        adviceLink = ["https://www.everydayhealth.com/type-2-diabetes/treatment/ways-lower-your-a1c/",
                     "https://www.webmd.com/cholesterol-management/lowering-triglyceride-levels",
                     "https://www.medicalnewstoday.com/articles/150109#diet"]
    else:
        #HE_DMfh_diabetic = 0
        #HE_wc_diabetic = 87.8986268174475
        HE_HP_diabetic = 3.0
        pa_totMET_diabetic = 1533.4665589660744
        HE_HTG_diabetic = 0
        #DI3_dg_diabetic = 0
        #DI4_dg_diabetic = 0
        sm_presnt_diabetic = 0
        HE_obe_diabetic = 4
        HE_HCHOL_diabetic = 0
        HE_BMI_diabetic = 25.21610630227172
        diabeticValue = [HE_HP_diabetic, pa_totMET_diabetic, HE_HTG_diabetic, sm_presnt_diabetic, HE_obe_diabetic, HE_HCHOL_diabetic, HE_BMI_diabetic]
        featureName = ["Hypertension status", "Total MET (min/week)", "Hyper triglycerides status", "Current smoking status", 
                       "Obesity status", "Hyperlipidemia status", "Body mass index (kg/m2)"]
        adviceList = ["About hypertension"] #same order
        adviceLink = ["https://www.medicalnewstoday.com/articles/150109#diet"]
    topAdvice = []
    topAdviceLink = []
    count = 0
    for i in range(len(featureValue)):
        if count == 3:
            break
        if  featureValue[i] > diabeticValue[i]:
            topAdvice.append(adviceList[i])
            topAdviceLink.append(adviceLink[i])            
            count += 1
    return topAdvice, topAdviceLink

print(top_advice(featureValue))

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
    data = db.collection("users").document(person["uid"]).get().to_dict()
    risk_score_goal = data['risk_score_goal']
    return render_template('profile.html', risk_score_goal = risk_score_goal, username = person["username"], fullname = person["fullname"], email = person["email"], dob = person["dob"])

@app.route('/change_username', methods=['GET', 'POST'])
def change_username():
    if request.method == 'POST':
        result = request.form
        username = result.get('username')
        person['username'] = username
        try: 
            #change username to the firebase realtime database
            data = {"username": username}
            db.collection("users").document(person["uid"]).update(data)
            return redirect(url_for('profile_page'))
        except Exception as e:
            print(e)
            return redirect(url_for('profile_page'))
    
@app.route('/change_riskscore', methods=['GET', 'POST'])
def change_riskscore():
    if request.method == 'POST':
        result = request.form
        risk_score_goal = result.get('risk_score_goal')
        person['risk_score_goal'] = risk_score_goal
        try: 
            #change username to the firebase realtime database
            data = {"risk_score_goal": risk_score_goal}
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


