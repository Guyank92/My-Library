from datetime import datetime, timedelta
import os
from flask import Flask, request, render_template, redirect, url_for, jsonify, flash,session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import jwt
from functools import wraps
from flask_jwt_extended import create_access_token, JWTManager
import json,time,os
loaned = False


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.sqlite3'
app.config['SECRET_KEY'] = "random string"
my_data = "my_data"
my_list_data = []
app_directory = os.path.dirname(__file__)
app.config['SESSION_TYPE'] = 'filesystem'
db = SQLAlchemy(app)
app.secret_key = 'secret_secret_key'
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
app_directory = os.path.dirname(__file__)
app.config['UPLOAD_FOLDER'] = '/uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    author = db.Column(db.String(255))
    year_published = db.Column(db.Integer)
    book_type = db.Column(db.Integer)


    def __init__(self, name, author, year_published, book_type):
        self.name = name
        self.author = author
        self.year_published = year_published
        self.book_type = book_type
        
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    city = db.Column(db.String(255))
    age = db.Column(db.Integer)
    loans = db.relationship('Loan', backref='customer', lazy=True)

    def __init__(self, name, city, age):
        self.name = name
        self.city = city
        self.age = age

class Loan(db.Model):
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id'), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), primary_key=True)
    loan_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)

    def calculate_max_loan_days(self):
        # Dictionary to map book types to maximum loan days
        type_max_days = {1: 10, 2: 5, 3: 2}
        book_type = Book.query.get(self.book_id).book_type
        return type_max_days.get(book_type, 0)
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def is_late(self):
        # Check if the loan is late based on the return_date and maximum allowed loan days
        if self.return_date:
            max_loan_days = self.calculate_max_loan_days()
            return self.return_date > (self.loan_date + timedelta(days=max_loan_days))
        return False


@app.route('/')
def menue():
    return render_template('home.html')

# Route to handle the home page
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        customer_name = request.form['customer_name']

        # Redirect to customer_detail page with the provided customer name
        return redirect(url_for('customer_detail', customer_name=customer_name))
    
    if request.method == 'POST':
        book_name = request.form['book_name']

        # Redirect to customer_detail page with the provided customer name
        return redirect(url_for('book_details', book_name=book_name))
    
    return render_template('home.html')

# Add a route to display all books
@app.route('/books')
def display_all_books():
    if not session.get('logged_in'):
        flash('You need to log in first!', 'error')
        return redirect(url_for('login'))
    
    # Query all books from the database
    all_books = Book.query.all()

    # Pass the list of books to the template
    return render_template('books.html', books=all_books)


@app.route('/loans', methods=['GET', 'POST'])
def display_all_loans():
    if not session.get('logged_in'):
        flash('You need to log in first!', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        action = request.form.get('action')


        if action == 'loan':
            loan_book()
        elif action == 'return':
            return_book()
        else:
            return 'Invalid action.'

        # Redirect to the /loans route to display the updated list of loans
        return redirect(url_for('display_all_loans'))

    # Query all loans from the database
    all_loans = Loan.query.all()
    return render_template('loans.html', loans=all_loans)


def return_book():
    global my_list_data
    # Get the book_id from the form or wherever it is available
    book_id = request.form['book_id']

    # Get the logged-in customer
    customer = get_customer()

    # Get the book based on the provided book_id
    book = Book.query.get(book_id)
    global loaned
    if customer and book:
        if loaned:
            # Find the existing loan
            existing_loan = Loan.query.filter_by(cust_id=customer.id, book_id=book_id).first()

            # Update the return_date to the current date
            existing_loan.return_date = datetime.utcnow().date()

            # Commit the changes to the database
            db.session.commit()
            my_list_data.append(f"{book.name} has returned to the library!")
            write_json_file()
            loaned = False

            flash('Book successfully returned!', 'success')
        else:
            flash('Book has returned to the library!', 'error')
    else:
        flash('Unable to return the book.', 'error')

    # Redirect to the /loans route to display the updated list of loans
    return redirect(url_for('display_all_loans'))

# Update the /loan_book route
@app.route('/loan_book', methods=['POST'])
def loan_book():
    global my_list_data
    # Get the book_id from the form or wherever it is available
    book_id = request.form['book_id']

    # Get the customer
    customer = get_customer()
    print(customer)
    # Get the book based on the provided book_id
    book = Book.query.get(book_id)
    
    if customer and book:
        global loaned
        if not is_book_already_loaned(customer.id, book_id):
            # Create a new loan entry
            new_loan = Loan(cust_id=customer.id, book_id=book_id, loan_date=datetime.utcnow().date())

            # Add the new loan to the session
            db.session.add(new_loan)

            # Commit the changes to the database
            db.session.commit()
            my_list_data.append(f"{customer.name} has loaned a book from the library!")
            write_json_file()
            flash('Book successfully loaned!', 'succes')
            loaned = True
        else:
            flash('Book is already loaned!', 'error')
    else:
        flash('Unable to loan the book.', 'error')

    # Redirect to the /loans route to display the updated list of loans
    return redirect(url_for('display_all_loans'))

def get_customer():
    # Get the customer name from the session
    customer_name = session.get('name')

    # Query the Customer table using the retrieved name
    return Customer.query.filter_by(name=customer_name).first()


def is_book_already_loaned(customer_id, book_id):
    existing_loan = Loan.query.filter_by(cust_id=customer_id, book_id=book_id).first()
    return existing_loan is not None


@app.route('/late_loans')
def display_late_loans():
    if not session.get('logged_in'):
        flash('You need to log in first!', 'error')
        return redirect(url_for('login'))
    # Get the logged-in customer
    customer = get_customer()

    if customer:
        # Get all loans for the customer
        customer_loans = Loan.query.filter_by(cust_id=customer.id).all()

        # Filter out late loans
        late_loans = [loan for loan in customer_loans if loan.is_late()]

        return render_template('late_loans.html', late_loans=late_loans)
    else:
        flash('Unable to fetch late loans.', 'error')
        return redirect(url_for('display_all_loans'))

@app.route('/customers')
def get_customers():
    if not session.get('logged_in'):
        flash('You need to log in first!', 'error')
        return redirect(url_for('login'))
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)


# Route to handle the customer detail page
@app.route('/customer_detail', methods=['POST'])
def customer_detail():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        found_customer = find_customer_by_name(customer_name)

        if found_customer:
            return render_template('customer_detail.html', customer=found_customer)
        else:
            flash('No customer found', 'failed')

    return render_template('home.html')  # Render an empty form on GET request

# Method to find a cust omer by name
def find_customer_by_name(customer_name):
    customer = Customer.query.filter_by(name=customer_name).first()
    return customer


# Route to handle the customer detail page
@app.route('/book_details', methods=['POST'])
def book_detail():
    if request.method == 'POST':
        book_name = request.form['book_name']
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        found_book = find_book_by_name(book_name)

        if found_book:
            return render_template('book_details.html', book=found_book)
        else:
            flash('No Book found', 'failed')

    return render_template('home.html')  # Render an empty form on GET request

# Method to find a customer by name
def find_book_by_name(found_book):
    book = Book.query.filter_by(name=found_book).first()
    return book


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    global my_list_data
    
    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']
        year_published = request.form['year_published']
        book_type = request.form['book_type']

        # Assuming you have a Book model defined
        new_book = Book(name=name, author=author, year_published=year_published, book_type=book_type)

        db.session.add(new_book)
        db.session.commit()
        flash('Book is successfully added to library!', 'succsses')
        read_json_file()
        my_list_data.append(f"{name} has been added to the library!")
        write_json_file()

        return redirect(url_for('display_all_books'))

    return render_template('add_book.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        city = request.form['city']
        age = request.form['age']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            error_message = "Password and Confirm Password do not match."
            return render_template('signup.html', error_message=error_message)
        
        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username is already taken', 'failed')

        # # Hash and salt the password using Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # # Create a new user and add to the database
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Customer added successfully', 'success')
        add_new_customer(name, city, age)
        return redirect(url_for('login'))  # Redirect to login page after successful signup
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global my_list_data
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]

        # Check if the user exists
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            # Generate an access token with an expiration time
            expires = timedelta(hours=1)
            access_token = create_access_token(identity=user.id, expires_delta=expires)  
            jsonify({'access_token': access_token, 'username': username}), 200
            session['logged_in'] = True
            my_list_data.append(f"{username} has logged in")
            flash('login successfully', 'success')
            write_json_file()
            all_books = Book.query.all()
        # Pass the books to the template
            return render_template('home.html', books=all_books)
        else:
            flash('Invalid username or password', 'failed')
    return render_template('login.html')
    

@app.route('/logout')
def logout():
    session.clear()
    flash('You logged out', 'success')
    return redirect(url_for('login'))       

def add_new_customer(name, city, age):
    global my_list_data
    new_customer = Customer(name=name, city=city, age=age)
    # Add the new customer to the database session
    db.session.add(new_customer)
    # Commit the changes to the database
    db.session.commit()
    my_list_data.append(f"{name} has signed up!")
    write_json_file()
    session['name'] = name
    return "A new customer was created."

def read_json_file():
    global my_data
    try:
        with open(my_data, 'r') as file:
         existing_data = json.load(file)
         my_list_data.append(existing_data)
    except: pass

def write_json_file():
    with open(my_data, 'w') as json_file:
        #Use json.dump to write the data to the file
        json.dump(my_list_data, json_file)


# Generate a JWT
def generate_token(customer_id):
    expiration = int(time.time()) + 3600  # Set the expiration time to 1 hour from the current time
    payload = {'user_id': customer_id, 'exp': expiration}
    token = jwt.encode(payload, 'secret-secret-key', algorithm='HS256')
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return flash('Token is missing', 'failed')

        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            flash('Token has expired', 'failed')
        except jwt.InvalidTokenError:
            return flash('Invalid token', 'failed')

        return f(current_user_id, *args, **kwargs)
    return decorated


def model_to_dict(model):
    serialized_model = {}
    for key in model.__mapper__.c.keys():
        serialized_model[key] = getattr(model, key)
    return serialized_model


def main():
    try:
        # Apply migrations before running the app
        with app.app_context():
            db.create_all()
            db.session.commit()

        app.run(debug=True, port=9000)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()