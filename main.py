from flask import Flask, render_template
import pandas as pd
from flask import Flask, request, session, render_template
from flask_mysqldb import MySQL
from prophet.plot import plot_plotly, plot_components_plotly
from prophet import Prophet


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure MySQL connection
app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your password'
app.config['MYSQL_DB'] = 'Name '

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM government_login WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            session['username'] = user[1]  # store username in session
            return render_template('upload.html')
        else:
            return render_template('login.html', msg='Incorrect username or password.')
    else:
        return render_template('login.html')



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get uploaded file
        file = request.files['file']


        # Read CSV data into pandas dataframe
        df = pd.read_csv(file)

        # Connect to MySQL
        cursor = mysql.connection.cursor()

        # #Create forecast table if it doesn't exist
        # cursor.execute('''CREATE TABLE IF NOT EXISTS forecast
        #                 (id INT AUTO_INCREMENT PRIMARY KEY,
        #                 date DATE,
        #                 cases INT,
        #                 deaths INT)''')

        # Insert data into forecast table
        for row in df.itertuples():
            cursor.execute('''INSERT INTO forecast (year, month, interest)
                            VALUES (%s, %s, %s)''', (row[1], row[2], row[3]))

        # Commit changes and close connection
        mysql.connection.commit()
        cursor.close()

        df['date'] = df['Year'].astype(str) + '-' + df['Month'].astype(str)
        df['date'] = pd.DatetimeIndex(df['date'])
        df = df[["date", "Interest"]]
        df.columns = ['ds', 'y']

        # Fit model
        train = df.iloc[:len(df) - 20]
        m = Prophet()
        m.fit(train)

        # Make predictions
        future = m.make_future_dataframe(periods=77, freq='MS')  # MS for monthly, H for hourly
        forecast = m.predict(future)

        return render_template('forecasting.html', forecast=forecast, uploaded=True)
    else:
        return render_template('upload.html')



if __name__ == '__main__':
   app.run()