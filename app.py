from flask import Flask, render_template, url_for

app = Flask(__name__)


@app.route('/')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/diagnosis')
def diagnosis_page():
    return render_template('diagnosis.html')


@app.route('/simulation')
def simulation_page():
    return render_template('simulation.html')


@app.route('/report')
def report_page():
    return render_template('report.html')


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


