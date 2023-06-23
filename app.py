from flask import Flask, render_template, request, redirect, session
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import requests
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secretSessionMenagementKey"
app.static_folder = 'static'

# Database connection
conn = sqlite3.connect('database.db')
conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
conn.close()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if('username' in session):
        session.pop('username', None)
        return redirect('/')
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    
    if user is not None:
        hashed_password = user[1]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            session['username'] = username
            username = ''
            password = ''
            return redirect('/dashboard')
        else:
            return render_template('login.html', usernameValid = True, passwordValid = False, passwordErrorMessage = 'Invalid password!', passwordValue = password, usernameValue = username)
    else:
        return render_template('login.html', usernameValid = False, passwordValid = True, usernameErrorMessage = 'Username doesn\'t exist!', passwordValue = password, usernameValue = username)

@app.route('/dashboard')
def dashboard():
    if('username' not in session):
        return redirect('/')
    
    dateTimeToday = datetime.today(); 
    dates = [dateTimeToday - timedelta(days=7), dateTimeToday - timedelta(days=15), dateTimeToday - timedelta(days=30)]
    lastDays = [7, 15, 30]
    avgs = [0, 0, 0]
    medians = [0, 0, 0]
    graphs = ["", "", ""]
    
    for index, days in enumerate(lastDays):
        # r = requests.get('http://api.nbp.pl/api/cenyzlota/' + x.strftime("%y-%m-%d") + '/' + dateTimeToday.strftime("%y-%m-%d") + '/')
        r = requests.get('http://api.nbp.pl/api/cenyzlota/last/' + str(days) + '/?format=json/')
        x = r.json()
        df = pd.DataFrame(x)
        df = df[['data', 'cena']]
        df['data'] = pd.to_datetime(df['data'])
        # Plot the data
        df.plot(x='data', y='cena', marker='o')
        
        # Add labels and title
        plt.xlabel('Date')
        plt.ylabel('Price PLN/g')
        plt.title('Gold price for the last ' + str(days) +' days')
        plt.legend().remove()
        graph_file = 'static/graph' + str(days) + 'dni.png'
        plt.savefig(graph_file)
        graphs[index] = graph_file

        #calc values
        avgs[index] = round(df['cena'].mean(), 2)
        medians[index] = round(df['cena'].median(), 2)

    return render_template('dashboard.html', username=session['username'], graph_files=graphs, avgs = avgs, medians = medians, len = len(graphs))

@app.route('/register')
def register():
    if('username' in session):
        session.pop('username', None)
        return redirect('/')
    return render_template('register.html')

@app.route('/process_register', methods=['POST'])
def process_register():
    if('username' in session):
        session.pop('username', None)
        return redirect('/')
    
    username = request.form['username']
    password = request.form['password']
    password_repeat = request.form['password_repeat']

    passwordOk = True
    usernameOk = True

    if(username.__len__() < 4):
        usernameOk = False

    if(password.__len__() < 5):
        passwordOk = False

    if(not passwordOk or not usernameOk):
        return render_template('register.html', usernameValid = usernameOk, passwordValid = passwordOk, passwordRepeatValid = True, passwordErrorMessage = 'Password must be at least 5 characters long!', usernameErrorMessage = 'Username must be at least 3 characters long!', passwordValue = password, usernameValue = username, repeatPasswordValue = password_repeat)

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cur.fetchone()

    if existing_user:
        conn.close()
        return render_template('register.html', usernameValid = False, passwordValid = True, passwordRepeatValid = True, usernameErrorMessage = 'User already exists!', passwordValue = password, usernameValue = username, repeatPasswordValue = password_repeat)


    if(password.__eq__(password_repeat)):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()

        #session['username'] = username
        #return redirect('/')
        return render_template('login.html', usernameValid = True, passwordValid = False, passwordValue = '', usernameValue = username, createdUser = True)

    else:
        return render_template('register.html', usernameValid = True, passwordValid = True, passwordRepeatValid = False, repeatPasswordErrorMessage = 'Passwords must match!', passwordValue = password, usernameValue = username, repeatPasswordValue = password_repeat)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
