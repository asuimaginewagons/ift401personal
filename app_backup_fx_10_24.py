from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sys
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://root:password@localhost/superstocks'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to the login page if not logged in

# Define the User model
class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    user_email = db.Column(db.String(128), primary_key=True)
    fname = db.Column(db.String(128), nullable=False)
    lname = db.Column(db.String(128), nullable=False)
    isadmin = db.Column(db.Boolean)
    islocked = db.Column(db.Boolean)
    cash = db.Column(db.DECIMAL(10,2), nullable=False)
    password = db.Column(db.String(512), nullable=False)

    def get_id(self):
        return self.user_email
# Define other models
class User_Stock(db.Model):
    __tablename__ = 'user_stock'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(128), db.ForeignKey('users.user_email'))
    stock_ticker = db.Column(db.CHAR(5), db.ForeignKey('market_stock.stock_ticker'))
    user_quantity = db.Column(db.Integer, nullable=False)
# Define user transactions
class User_Transactions(db.Model):
    __tablename__ = 'user_transactions'
    transaction_number = db.Column(db.Integer, primary_key=True, AUTO_INCREMENT=True) 
    stock_ticker = db.Column(db.CHAR(5), db.ForeignKey('market_stock.stock_ticker'))
    sell_buy = db.Column(db.Boolean)
    price_at_purchase = db.Column(db.DECIMAL(10,2), nullable=False)
    purchase_quantity = db.Column(db.Integer, nullable=False)
    user_email = db.Column(db.String(128), db.ForeignKey('users.user_email'))
# Define market stock
class Market_Stock(db.Model):
    __tablename__ = 'market_stock'
    stock_ticker = db.Column(db.CHAR(5), primary_key=True)
    stock_name = db.Column(db.String(128), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    stock_price = db.Column(db.DECIMAL(10,2), nullable=False)
    market_high = db.Column(db.DECIMAL(10,2), nullable=False)
    market_low = db.Column(db.DECIMAL(10,2), nullable=False)
# Define market
class Market(db.Model):
    __tablename__ = 'market'
    DOY = db.Column(db.Integer, primary_key=True)
    isOpen = db.Column(db.Boolean)
    openHour = db.Column(db.Integer, nullable=False)
    closeHour = db.Column(db.Integer, nullable=False)

# Load user callback
@login_manager.user_loader
def load_user(user_email):
    return Users.query.get(user_email)

# Database init
@app.route('/createdb')
def creDB():
    db.create_all()
    return "Created product database"
# Homepage
@app.route('/')
def home():
    current_year = datetime.now().year
    return render_template('home.html', current_year=current_year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Grab email and password from webpage
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Login logic. Finds user then checks password against hashed password in the database
        user = Users.query.filter_by(user_email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)  # Log the user in
            print('Successful Login')
            flash('Login successful', 'success')
            return redirect(url_for('dashboard_view'))
        else:
            print('Login failed')
            flash('Login failed. Check your email or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        EnteredPassword = request.form['password']
        HashedPassword = generate_password_hash(EnteredPassword)
        userObj = Users(
            user_email=username,
            password=HashedPassword,
            fname="dne",
            lname="dne",
            isadmin=False,
            cash=0
        )
        # attempt to add to database
        try:
            db.session.add(userObj)
            print('User added successfully') # Debug message
            db.session.commit()
            flash(f'Registration successful for {username}', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            print(f'Error adding user: {e}') # Debug message
            flash('Registration failed. Please try again.', 'danger')
    return render_template('register.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/dashboard')
@login_required
def dashboard_view():
    username = current_user.user_email  # Use the logged-in user's email
    user = db.session.query(Users).filter(Users.user_email == username).first()
    cash = user.cash

    AllMarketStocks = db.session.query(Market_Stock).all()

    userStocks = db.session.query(User_Stock).filter(User_Stock.user_email == username).all()
    listOfUserStock = []
    stockData = []
    for item in userStocks:
        listOfUserStock.append(item.stock_ticker)
        stockData.append(item.user_quantity)

    return render_template('dashboard.html', username=username, cash=cash, allstocks=AllMarketStocks, ownedStocklables=listOfUserStock, data=stockData)

@app.route('/buy_stocks')
def buy_stocks():
    return "Buy Stocks page (To be implemented)"

@app.route('/add_cash', methods=['GET', 'POST'])
def add_cash():
    username = current_user.user_email  # Use the logged-in user's email
    current_cash = 1000.00  # This should ideally be fetched from the database
    if request.method == 'POST':
        amount = float(request.form['amount'])
        import random
        success_rate = random.choice([True, False])

        if success_rate:
            new_cash = current_cash + amount
            flash(f'Success! ${amount} has been added to your account. Your new balance is ${new_cash:.2f}.', 'success')
            return redirect(url_for('dashboard_view'))
        else:
            flash('Error: Failed to add cash. Please try again.', 'danger')
            return redirect(url_for('add_cash'))

    return render_template('add_cash.html', username=username, current_cash=current_cash)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        flash(f'A password reset link has been sent to {email}', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/sell_stocks', methods=['GET', 'POST'])
def sell_stocks():
    if request.method == 'POST':
        #get info from user
        stock = request.form.get('stock_ticker')
        print("selected stock: ",stock)
        num_stocks = request.form.get('num_stocks')
        print(num_stocks)
        userEmail = "greg@greg.greg"

        #get row from db
        user_inventoryObj = db.session.query(User_Stock).filter(User_Stock.stock_ticker == stock).first()
        print(user_inventoryObj)
        oldStockCount = user_inventoryObj.user_quantity
        newStockCount = oldStockCount - int(num_stocks)
        print("new stock count:", newStockCount)
        setattr(user_inventoryObj, 'user_quantity', newStockCount)
        db.session.commit()
        print("sold stock from user")

<<<<<<< HEAD
        num_stocks = int(num_stocks)
        total_stocks = 50  # Replace with actual stock quantity logic

        if num_stocks > total_stocks:
            flash(f"Not enough stocks available to sell. You have {total_stocks} stocks.", "danger")
            return redirect(url_for('not_enough_stocks'))
        else:
            sell_value = num_stocks * 500  # Replace with actual sell value logic
            flash(f'Successfully sold {num_stocks} stocks for ${sell_value}.', 'success')
            return redirect(url_for('dashboard_view'))

    return render_template('sell_stocks.html', error=False)
# Error page
=======
        #add cash to user
        user_obj = db.session.query(Users).filter(Users.user_email == userEmail).first()
        market_stockObj = db.session.query(Market_Stock).filter(Market_Stock.stock_ticker == stock).first()
        cashValue = market_stockObj.stock_price * int(num_stocks)
        setattr(user_obj, 'cash', user_obj.cash + cashValue)
        db.session.commit()
        print("added cash to user profile")

        #add new transaction log
        newTransaction = User_Transactions(
            stock_ticker = stock,
            sell_buy = False,
            price_at_purchase = market_stockObj.stock_price,
            purchase_quantity = num_stocks,
            user_email = userEmail
        )
        db.session.add(newTransaction)
        db.session.commit()
        print("added transaction log")

        return redirect(url_for('dashboard_view'))

        #if not num_stocks or not num_stocks.isdigit():
        #    flash("Please enter a valid number of stocks.", "danger")
        #    return render_template('sell_stocks.html', error=False)

        #num_stocks = int(num_stocks)
        #total_stocks = 50

        #if num_stocks > total_stocks:
        #    flash(f"Not enough stocks available to sell. You have {total_stocks} stocks.", "danger")
        #    return redirect(url_for('not_enough_stocks'))
        #else:
        #    sell_value = num_stocks * 500
        #    flash(f'Successfully sold {num_stocks} stocks for ${sell_value}.', 'success')
        #    return redirect(url_for('dashboard_view'))

    if request.method == 'GET':
        enteredStock = request.args.get('stockToAction', None)
        print(enteredStock)
        userStockObj = db.session.query(User_Stock).filter(User_Stock.stock_ticker == enteredStock).first()
        stockObj = db.session.query(Market_Stock).filter(Market_Stock.stock_ticker == enteredStock).first()
        print(stockObj.stock_price)
        count = userStockObj.user_quantity
        print(count)
        value = stockObj.stock_price * count
        print(value)
        return render_template('sell_stocks.html', error=False, stockToAction=enteredStock,ownedCount=count,summedValue = value)

>>>>>>> 177536f5bc762fcce95450371bd8d21f22e289c7
@app.route('/not_enough_stocks')
def not_enough_stocks():
    return render_template('not_enough_stocks.html')



# User settings
@app.route('/user_settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        new_email = request.form['email']
        new_password = request.form['password']
        flash('User settings updated successfully', 'success')
        return redirect(url_for('dashboard_view'))
    return render_template('user_settings.html')
# Admin page
@app.route('/admin_page')
@login_required
def admin_page():
    if not current_user.isadmin:
        return "ADMIN ACCESS ONLY", 403
    return render_template('admin_page.html')
# Add stock
@app.route('/admin/addstock', methods=['GET', 'POST'])
@login_required
def admin_add_stock():
    # Grab info from webpage
    if request.method == 'POST':
        stockName = request.form['stockName']
        stockTicker = request.form['stockTicker']
        stockPrice = request.form['stockPrice']
        stockCount = request.form['stockCount']
        stockObj = Market_Stock(
            stock_ticker=stockTicker,
            stock_name=stockName,
            stock_price=stockPrice,
            stock_quantity=stockCount,
            market_high=stockPrice,
            market_low=stockPrice,
        )
        # Add info to database
        db.session.add(stockObj)
        db.session.commit()
        flash('Stock added successfully!', 'success')
        return redirect(url_for('admin_page'))
    return render_template('admin_add_stock.html')

@app.route('/admin/view_users', methods=['GET','POST'])
@login_required
def view_users():
    if not current_user.isadmin:
        return "ADMIN ACESS ONLY", 403

    all_users = Users.query.all()
    return render_template('view_users.html', users=all_users)


if __name__ == '__main__':
    app.run(debug=True)