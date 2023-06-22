from flask import Flask, render_template, request, redirect, session
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key"
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
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    conn.close()

    if user:
        session['username'] = username
        return redirect('/dashboard')
    else:
        return 'Invalid username or password'

@app.route('/dashboard')
def dashboard():
    r = requests.get('http://api.nbp.pl/api/exchangerates/rates/a/gbp/last/10/?format=json')
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

    if 'username' in session:
        df = pd.DataFrame({
            'Name': ['John', 'Alice', 'Bob'],
            'Age': [25, 30, 35]
        })
        column_headers = df.columns
        data_rows = df.to_dict(orient='records')
        return render_template('dashboard.html', username=session['username'], column_headers=column_headers, data_rows=data_rows, graph_file=graph_file)
    else:
        return redirect('/')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/process_register', methods=['POST'])
def process_register():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cur.fetchone()

    if existing_user:
        conn.close()
        return 'Username already exists!'

    cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

    session['username'] = username
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
