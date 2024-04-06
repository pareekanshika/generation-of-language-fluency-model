from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import speech_recognition as sr
import time
import openai
import re
from flask_mysqldb import MySQL, MySQLdb

app = Flask(__name__)

openai.api_key = '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'

app.secret_key = "root_anshi"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'anshi'
app.config['MYSQL_PASSWORD'] = 'root_anshi'
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pwd = request.form['pwd']
        global email_cons, pwd_cons
        email_cons=email
        pwd_cons=pwd
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user_details WHERE emailid = %s and pwd= %s", (email, pwd))
        user = cursor.fetchone()
        cursor.close()

        if user is not None and user['pwd'] == pwd:
            session['logged_in'] = True
            session['email'] = email
            return redirect(url_for('index_c'))
        else:
           flash("Invalid username or password. Please try again.", "error")

    return render_template("login.html")


@app.route('/add_fluency', methods=["GET","POST"])
def add_fluency():
    data = request.json
    fluency = data['fluency']
    cursor = mysql.connection.cursor()
    
    # Check if the user exists
    cursor.execute("SELECT * FROM user_details WHERE emailid = %s and pwd = %s", (email_cons,pwd_cons))
    user = cursor.fetchone()

    if user:
        # Check the number of uses
        cursor.execute("SELECT f1, f2, f3 FROM user_details WHERE emailid = %s and pwd= %s", (email_cons,pwd_cons))
        fluency_uses = cursor.fetchone()
        if fluency_uses:
            if fluency_uses.get('f1') is None:
                cursor.execute("UPDATE user_details SET f1 = %s WHERE emailid = %s and pwd=%s", (fluency, email_cons,pwd_cons))
            elif fluency_uses.get('f2') is None:
                cursor.execute("UPDATE user_details SET f2 = %s WHERE emailid = %s", (fluency, email_cons))
            elif fluency_uses.get('f3') is None:
                cursor.execute("UPDATE user_details SET f3 = %s WHERE emailid = %s", (fluency, email_cons))
            else:
                flash("You have reached the maximum limit of fluency uses.","error")
                cursor.close()
                return redirect(url_for('login', error="You have reached the maximum limit of fluency uses."))
            mysql.connection.commit()
            cursor.close()
            flash("Fluency added successfully.","error")
            return render_template("fluency.html")
        
        else:
            # If no fluency uses record found, set f1 to fluency
            cursor.execute("UPDATE user_details SET f1 = %s WHERE emailid = %s", (fluency, email_cons))
            mysql.connection.commit()
            cursor.close()
            flash("Fluency added successfully.","error")
            return render_template("fluency.html")
    else:
        flash("User not authenticated.","error")
        cursor.close()
        return render_template("login.html")
   

@app.route('/home',methods=['GET','POST'])
def index_c():
    return render_template("index_c.html")

@app.route('/twisters',methods=['GET','POST'])
def twisters():
    return render_template("twisters.html")

@app.route('/calculate_accuracy', methods=['POST'])
def calculate_accuracy():
    data = request.json
    twister_content = data.get('twisterContent', '')
    tx2_content = data.get('tx2Content', '')
    word_count = len(twister_content.split())
    acc = len(set(twister_content.split()) & set(tx2_content.split()))
    accuracy = (acc/word_count)*100
    rounded_accuracy = round(accuracy, 2)  # rounding accuracy to two decimal places
    return jsonify({"accuracy": rounded_accuracy})
    # return redirect(url_for('fluency', accuracy=accuracy))

@app.route('/fluency')
def fluency():   
        accuracy=float(request.args.get('accuracy'))if 'accuracy' in request.args else None
        return render_template("fluency.html",accuracy=accuracy )
   

@app.route('/search')
def search():
    return render_template("search.html")

@app.route('/blog')
def blog():
    return render_template("blog.html")

@app.route('/pwd_rec', methods=['GET', 'POST'])
def pwd_rec():
    if request.method == 'POST':
        email = request.form.get('email')
        security_answer = request.form.get('security_answer')
        new_password = request.form.get('password')

        if not new_password:
            flash('Please enter a new password.')
            return render_template('pwd_rec.html')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user_details WHERE emailid = %s and security_details=%s ", (email,security_answer))
        user = cursor.fetchone()

        if user is not None:
            if user['security_details'] == security_answer:
                cursor.execute("update user_details SET pwd= %s where emailid= %s", (new_password, email))
                mysql.connection.commit()
                flash('Password updated successfully. You can now log in with your new password.')
                cursor.close()
                return redirect(url_for('login'))
            else:
                flash('Email not found. Please check the entered email address.')
                cursor.close()
        else:
            
            flash('Security answer is incorrect. Please check your credentials.')
            cursor.close()

    return render_template('pwd_rec.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))
@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")
    else:
        email = request.form['email']
        psw = request.form['psw']
        psw_confirm = request.form['psw1']
        no = request.form['number']
        na = request.form['name']
        security_answer = request.form['security_answer']
         # Email validation
        if not re.match(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            flash("Invalid email format.", "error")
            return redirect(url_for('signup'))
       
        # Password validation
        if len(psw) < 8 or not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+{}[\]|\\:;\"'<>,.?/~`]).{8,}$", psw):
            flash("Password must have at least 8 characters including at least one lowercase letter, one uppercase letter, one digit, and one symbol.", "error")
            return redirect(url_for('signup'))

        if len(no) != 10 or not no.isdigit():
            flash("Phone number must be of 10 digits.","error")
            return redirect(url_for('signup'))
        if psw != psw_confirm:
            flash("Passwords do not match.","error")
            return redirect(url_for('signup'))
        cur = mysql.connection.cursor()
        cur.execute("insert into user_details(emailid,pwd,name,pno,security_details) Values(%s,%s,%s,%s,%s)", (email, psw, na, no,security_answer))
        mysql.connection.commit()
        session['email'] = request.form['email']
        session['psw'] = request.form['psw']
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
