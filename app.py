from flask import Flask, render_template, request, redirect, session
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import requests
import bcrypt

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
            return redirect('/dashboard')
        else:
            return render_template('dialog.html', title = 'Login error', content = 'Invalid password!')
            return 'Invalid password!'
    else:
        return render_template('dialog.html', title = 'Login error', content = 'User doesn\'t exist!')
        return 'User doesn\'t exist!'

@app.route('/dashboard')
def dashboard():
    r = requests.get('http://api.nbp.pl/api/exchangerates/rates/a/gbp/2012-01-01/2012-01-31/')
    # http://api.nbp.pl/api/exchangerates/rates/a/gbp/last/10/?format=json
    x = r.json()
    df = pd.DataFrame(x)
    df = pd.DataFrame(x['rates'])
    df = df[['effectiveDate', 'mid']]
    df['effectiveDate'] = pd.to_datetime(df['effectiveDate'])
    # Plot the data
    df.plot(x='effectiveDate', y='mid', marker='o')

    # Add labels and title
    plt.xlabel('Effective Date')
    plt.ylabel('Mid Value')
    plt.title('GBP Mid Value')

    graph_file = 'static/graph.png'
    plt.savefig(graph_file)

    #calc values
    average_mid = df['mid'].mean()
    median_mid = df['mid'].median()

    if 'username' in session:
        df = pd.DataFrame({
            'Name': ['John', 'Alice', 'Bob'],
            'Age': [25, 30, 35]
        })
        column_headers = df.columns
        data_rows = df.to_dict(orient='records')
        return render_template('dashboard.html', username=session['username'], column_headers=column_headers, data_rows=data_rows, graph_file=graph_file, avg = average_mid, med = median_mid)
    else:
        return redirect('/')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/process_register', methods=['POST'])
def process_register():
    username = request.form['username']
    password = request.form['password']
    password_repeat = request.form['password_repeat']

    if(password.__eq__(password_repeat)):
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            conn.close()
            return 'Username already exists!'

        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()

        session['username'] = username
        return redirect('/')
    else:
        return 'Repeat your password!'

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
