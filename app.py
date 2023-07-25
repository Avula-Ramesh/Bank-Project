from flask import Flask, render_template, request, flash,session, redirect
import mysql.connector
import bcrypt
from datetime import timedelta
import datetime as datetime
current_time = datetime.datetime.now()
special_characters = "@_!#$%^&*()<>?/\|}{~:"

app = Flask(__name__)
app.secret_key="Ram@666"

db = mysql.connector.connect(
    host="127.0.0.1",
    user='root',
    password='AmmuRam.16',
    database='Bank_Database'
)
cursor = db.cursor()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        Input_UserName = request.form.get("Username")
        Input_Password = request.form.get("Password")
        Query_Change_Password = "select password from bank where user_name ='{}'".format(Input_UserName)
        cursor.execute(Query_Change_Password)
        Data_Change_Password = cursor.fetchone()[0]
        if not bcrypt.checkpw(Input_Password.encode('utf-8'), Data_Change_Password.encode("utf-8")):
            return render_template('login.html', msg='Incorrect Password')

        q1 = f"select * from bank where (user_name='{Input_UserName}' and password='{Data_Change_Password}')"
        cursor.execute(q1)
        User_data = cursor.fetchall()

        if not User_data:
            return render_template('login.html', msg='Incorrect Password')

        msg = 'Logged in successfully !'
        session['username']=Input_UserName
        return redirect('/dashboard')
    else:
        return render_template('login.html', msg='')

def get_user_first_name(username):
    query = "SELECT first_name FROM bank WHERE user_name = %s"
    cursor.execute(query, (username,))

    result = cursor.fetchone()
    if result:
        first_name = result[0]
    else:
        first_name = None
    return first_name

def get_logged_in_username(session):
    if 'username' in session:
        return session['username']
    else:
        return None

@app.route('/dashboard')
def dashboard():
    username = get_logged_in_username(session)
    query='select account_no,first_name,last_name, address, account_type,balance from bank where user_name=%s'
    cursor.execute(query,(username,))
    account_data=cursor.fetchone()
    account_number=account_data[0]
    first_name=account_data[1]
    last_name=account_data[2]
    name=first_name +' '+ last_name
    address=account_data[3]
    account_type=account_data[4]
    balance=account_data[5]

    return render_template('dashboard.html', first_name=first_name,last_name=last_name,account_number=account_number, name=name,address=address, account_type=account_type,
                           balance=balance)


@app.route('/logout')
def logout():

    session.pop('username', None)

    return render_template('index.html')

@app.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    if request.method=='POST':
        user_name=request.form.get('user_name')
        new_password=request.form.get('new_password')
        confirm_password=request.form.get('confirm_password')

        query = 'SELECT * FROM bank WHERE user_name = %s'
        print(query)
        cursor.execute(query, (user_name,))
        account = cursor.fetchone()
        if account:
            pwd = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")
            pwd_ch_timestamp = datetime.datetime.now()
            pwd_exp_date = pwd_ch_timestamp + timedelta(days=45)
            query2='UPDATE bank set password=%s, password_changed="YES",password_change_timestamp=%s,password_expiration_date=%s WHERE user_name=%s'
            print(query2)
            cursor.execute(query2,(pwd,pwd_ch_timestamp,pwd_exp_date,user_name))
            db.commit()

            return render_template('reset_password.html',confirm_password=confirm_password)
        else:
            return render_template('reset_password.html')
    else:
        return render_template('reset_password.html')

def withdraw_form():

    return render_template('dashboard.html',)

@app.route('/withdraw', methods=['GET','POST'])
def withdraw():
    username = get_logged_in_username(session)
    query = 'select account_no,first_name, last_name,balance from bank where user_name=%s'
    cursor.execute(query, (username,))
    account_data = cursor.fetchone()
    account_number = account_data[0]
    first_name = account_data[1]
    last_name = account_data[2]
    balance = account_data[3]
    if request.method=='POST':
        amount = request.form.get('amount')
        if amount is None or not amount.isdigit():
            return 'Invalid Amount'
        amount=float(amount)

        if balance < amount:
            return 'Insufficient Balance'

        new_balance= balance - amount
        update_q1= 'UPDATE bank SET balance=%s WHERE account_no=%s'
        print(update_q1)
        cursor.execute(update_q1,(new_balance,account_number))
        db.commit()

        query = 'INSERT INTO transactions (username,account_number, type, amount, date) VALUES (%s,%s, %s, %s, %s)'
        transaction_type = 'Withdrawal'
        transaction_date = datetime.datetime.now()
        cursor.execute(query, (username,account_number,transaction_type, amount, transaction_date))
        db.commit()

        account_data = list(account_data)
        account_data[3] = new_balance
        balance = new_balance

    return render_template('withdraw.html',first_name=first_name,last_name=last_name,account_number=account_number,balance=balance)

@app.route('/deposit', methods=['GET','POST'])
def deposit():
    username = get_logged_in_username(session)
    query = 'select account_no,first_name ,last_name,balance from bank where user_name=%s'
    cursor.execute(query, (username,))
    account_data = cursor.fetchone()
    account_number = account_data[0]
    first_name = account_data[1]
    last_name = account_data[2]
    balance = account_data[3]
    if request.method=='POST':
        amount = request.form.get('amount')
        if amount is None or not amount.isdigit():
            return 'Invalid Amount'
        amount=float(amount)

        new_balance = balance + amount

        update_query = 'UPDATE bank SET balance = %s WHERE account_no = %s'
        cursor.execute(update_query, (new_balance, account_number))
        db.commit()

        query = 'INSERT INTO transactions (username,account_number, type, amount, date) VALUES (%s,%s, %s, %s, %s)'
        transaction_type = 'Deposit'
        transaction_date = datetime.datetime.now()
        cursor.execute(query, (username,account_number, transaction_type, amount, transaction_date))
        db.commit()
        account_data = list(account_data)
        account_data[3] = new_balance
        balance = new_balance

    return render_template('deposit.html',first_name=first_name,last_name=last_name,account_number=account_number,balance=balance)

@app.route('/transactions')
def transactions():
    username = get_logged_in_username(session)
    query = 'select first_name from bank where user_name=%s'
    cursor.execute(query, (username,))
    account_data = cursor.fetchone()
    first_name = account_data[0]

    query = 'SELECT id, account_number, type, amount, date FROM transactions WHERE username=%s ORDER BY date DESC'
    cursor.execute(query,(username,))
    transactions = []
    for row in cursor.fetchall():
        transaction = {
            'id': row[0],
            'account_number': row[1],
            'type': row[2],
            'amount': row[3],
            'date': row[4]
        }
        transactions.append(transaction)
    return render_template('transactions.html', transactions=transactions,first_name=first_name)


@app.route('/update/password',methods=['GET','POST'])
def update():
    username = get_logged_in_username(session)
    query = 'select first_name from bank where user_name=%s'
    cursor.execute(query, (username,))
    account_data = cursor.fetchone()
    first_name = account_data[0]

    if request.method=='POST':
        password = request.form.get('password')
        if password is None:
            return 'Error: password is required'
        pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")
        pwd_ch_timestamp = datetime.datetime.now()
        pwd_exp_date = pwd_ch_timestamp + timedelta(days=45)
        query2="update bank set password=%s,password_changed='YES',password_change_timestamp=%s,password_expiration_date=%s where user_name=%s"
        cursor.execute(query2,(pwd,pwd_ch_timestamp,pwd_exp_date,username))
        db.commit()
        return render_template('update.html',password=password)
    else:
        return render_template('update.html',first_name=first_name)

@app.route('/update/mobile_no',methods=['GET','POST'])
def update_mobile_no():
    username = get_logged_in_username(session)
    query = 'select first_name from bank where user_name=%s'
    cursor.execute(query, (username,))
    account_data = cursor.fetchone()
    first_name = account_data[0]


    if request.method=='POST':
        mobile_no=request.form.get('mobile_no')
        query3='UPDATE bank SET mobile_No=%s where user_name=%s'
        cursor.execute(query3,(mobile_no,username))
        db.commit()
    return render_template('update mobile no.html', first_name=first_name)


@app.route('/update/address',methods=['GET','POST'])
def update_address():
    username=get_logged_in_username(session)
    query = 'select first_name from bank where user_name=%s'
    cursor.execute(query, (username,))
    account_data = cursor.fetchone()
    first_name = account_data[0]

    if request.method=='POST':
        address=request.form.get('address')
        query3='UPDATE bank SET address=%s where user_name=%s'
        cursor.execute(query3,(address,username))
        db.commit()
    return render_template('update address.html',first_name=first_name)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        f_name = request.form.get('First Name')
        l_name = request.form.get('Last Name')
        user_name = request.form.get("Username")
        password = request.form.get("Password")
        input_amount = request.form.get("Deposit_Amount")
        input_account_type = request.form.get("Account Type")
        date_of_birth = request.form.get("Date_Of_Birth")
        input_address = request.form.get("Address")
        input_mobile_no = request.form.get("Mobile_No")
        input_email = request.form.get('Email')
        unique_code = 16

        # Validate First Name
        if f_name is not None and any(char in special_characters for char in f_name):
            flash("Special characters are not allowed in First Name")

        # Validate Last Name
        if l_name is not None and any(char in special_characters for char in l_name):
            flash("Special characters are not allowed in Last Name")

        # Validate Username
        if user_name is not None and any(char in special_characters for char in user_name):
            flash("Special characters are not allowed in Username")

        # Validate Password
        if password is None or len(password or '') < 6:
            flash("Password should contain at least 6 characters")
        elif not any(char.isdigit() for char in password):
            flash("Password should contain at least 1 number")
        elif not any(char.isupper() for char in password):
            flash("Password should contain at least 1 uppercase character")
        elif not any(char.islower() for char in password):
            flash("Password should contain at least 1 lowercase character")
        elif not any(char in special_characters for char in password):
            flash("Password should contain at least 1 special character")

        # Validate Date of Birth
        if date_of_birth is not None:
            try:
                date_of_birth = datetime.datetime.strptime(date_of_birth, "%d/%m/%Y").date()
            except ValueError:
                flash("Please enter Date of Birth in the proper format (DD/MM/YYYY)")
        else:
            flash("Date of Birth is required")

        # Validate Mobile Number
        if input_mobile_no is None or len(input_mobile_no) != 10 or not input_mobile_no.isdigit():
            flash("Please enter a 10-digit valid Mobile Number")

        encrypted_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")
        password_change_timestamp = current_time
        password_expiry_date = password_change_timestamp + timedelta(days=45)

        if input_mobile_no is not None:
            input_mobile_no = str(input_mobile_no)
        else:
            input_mobile_no = ""

        input_account_no = int(str(unique_code) + input_mobile_no)

        query_signup = "INSERT INTO bank (account_no, first_name, last_name, user_name, password, date_of_birth, address, mobile_no, email, account_type, password_change_timestamp, password_changed, password_expiration_date, balance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query_signup, (input_account_no, f_name, l_name, user_name, encrypted_password, date_of_birth, input_address, input_mobile_no, input_email, input_account_type, password_change_timestamp, "NO", password_expiry_date, input_amount))
        db.commit()
        msg = 'You have successfully signed up'
        return render_template('login.html', msg=msg)
    else:
        msg = 'Please fill out the form!'
        return render_template('signup.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True)
