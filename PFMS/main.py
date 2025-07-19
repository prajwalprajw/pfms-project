from flask import Flask,render_template,request,session,redirect,url_for,jsonify
from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,logout_user,login_manager,LoginManager
from flask_login import login_required,current_user
from sqlalchemy import text

from datetime import datetime
from flask import flash


transactions = []
savings_goals = [
    {"name": "Vacation Fund 🌴", "target": 50000, "saved": 000},
    {"name": "Emergency Fund 🚑", "target": 5000, "saved": 000},
]



#my db connection
local_server=True

app = Flask(__name__)
app.secret_key='prajwal'

login_manager=LoginManager(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:password@localhost/databas_table_name'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:prajwal%40123@localhost/pfms'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/pfms'

db=SQLAlchemy(app)


#here we will create db models that is table
class User(UserMixin,db.Model):
    id=db.Column(db.String,primary_key=True)
    username=db.Column(db.String(50))
    email=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(1000))

@app.route("/",methods=['POST','GET'])


def base():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            print("Email already exists")
            return render_template('/home.html')

        # Hash the password
        encpassword = generate_password_hash(password)

        # Using raw SQL with text() to insert into the database
        query = text(f"INSERT INTO user (username, email, password) VALUES ('{username}', '{email}', '{encpassword}');")
        db.session.execute(query)  # Execute the query
        db.session.commit()  # Commit the transaction

        return render_template('loging.html')

    return render_template('home.html')


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(100))
    amount = db.Column(db.FLOAT)
    type = db.Column(db.String(10))  # 'income' or 'expense'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


    
@app.route("/Dashboard")
@login_required
def Dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    transactions_data = [
        {
            "date": t.timestamp.strftime("%Y-%m-%d"),
            "amount": t.amount,
            "type": t.type
        } for t in transactions
    ]

    return render_template('dashboard.html', transactions=transactions_data, username=current_user.username)

  
@app.route("/Transactions", methods=['GET', 'POST'])
@login_required
def transactions_page():
    if request.method == 'POST':
        description = request.form.get('description')
        amount_raw = request.form.get('amount')
        t_type = request.form.get('type')

        if not amount_raw or not description or not t_type:
            flash("Please fill in all fields", "warning")
            return redirect(url_for('transactions_page'))

        try:
            amount = float(amount_raw)
        except ValueError:
            flash("Invalid amount", "danger")
            return redirect(url_for('transactions_page'))

        new_transaction = Transaction(
            user_id=current_user.id,
            description=description,
            amount=amount,
            type=t_type
        )
        db.session.add(new_transaction)
        db.session.commit()
        flash("Transaction added!", "success")
        return redirect(url_for('transactions_page'))

    # Get all user's transactions
    all_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()

    # Calculate balance
    total_balance = sum(t.amount if t.type == 'income' else -t.amount for t in all_transactions)

    # Convert to dictionary for HTML rendering
    transactions_data = [
        {
            "id": t.id,
            "description": t.description,
            "amount": t.amount,
            "type": t.type,
            "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for t in all_transactions
    ]

    return render_template("Transactions.html", transactions=transactions_data, total_balance=total_balance)


@app.route("/Budgets")
def  Budgets():
    
    return render_template('budgets.html')


@app.route("/Reports")
def  Reports():
    return render_template('reports.html')


@app.route('/Settings')
def Settings():
    return render_template('setting.html', savings_goals=savings_goals)

@app.route('/add_savings', methods=['POST'])
@login_required
def add_savings():
    index = int(request.form.get('index'))
    amount = float(request.form.get('amount'))

    # Update the in-memory goal — you'll replace this with a DB model eventually
    if index >= len(savings_goals):
        flash("Invalid savings goal", "danger")
        return redirect(url_for('Settings'))

    savings_goals[index]['saved'] += amount

    # Log it as an expense transaction
    new_transaction = Transaction(
        user_id=current_user.id,
        description=f"Added to {savings_goals[index]['name']}",
        amount=amount,
        type="expense"
    )
    db.session.add(new_transaction)
    db.session.commit()

    flash(f"${amount} added to {savings_goals[index]['name']}!", "success")
    return redirect(url_for('Settings'))


@app.route("/Authentication")
def  Authentication():
    return render_template('authentication.html')


@app.route("/Loging",methods=['POST','GET'])
def  Loging():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user=User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for('Dashboard'))
        else:
            print("invlaid credentials")
            return render_template('login.html')
    return render_template('loging.html')

@app.route("/Logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('Loging'))



@app.route('/dashboard-data')
@login_required
def dashboard_data():
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    data = [
        {
            "date": t.timestamp.strftime("%Y-%m-%d"),
            "amount": t.amount,
            "type": t.type
        } for t in user_transactions
    ]

    return render_template('dashboard.html', transactions=data, username=current_user.username)

@app.route('/api/finance')
@login_required
def finance_summary():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    total_balance = total_income - total_expense

    return jsonify({
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "total_balance": round(total_balance, 2)
    })



if __name__ == '__main__':
    app.run(debug=True)



app.run(debug=True)
