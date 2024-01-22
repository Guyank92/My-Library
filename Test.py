import unittest
from flask import Flask, session
from your_library_app import app, db, User, Book, Customer, Loan, allowed_file, generate_token, get_customer

class LibraryAppTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_db.sqlite3'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # Helper method to log in a test user
    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    # Helper method to log out
    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    # Helper method to create a test book
    def create_test_book(self):
        test_book = Book(name='Test Book', author='Test Author', year_published=2022, book_type=1)
        db.session.add(test_book)
        db.session.commit()
        return test_book

    def test_home_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to the Library', response.data)

    def test_signup_and_login(self):
        response = self.app.post('/signup', data=dict(
            username='testuser',
            password='testpassword',
            name='Test User',
            city='Test City',
            age=25,
            confirm_password='testpassword'
        ), follow_redirects=True)
        self.assertIn(b'Customer added successfully', response.data)

        response = self.login('testuser', 'testpassword')
        self.assertIn(b'login successfully', response.data)

    def test_add_book(self):
        self.login('testuser', 'testpassword')
        response = self.app.post('/add_book', data=dict(
            name='Test Book',
            author='Test Author',
            year_published=2022,
            book_type=1
        ), follow_redirects=True)
        self.assertIn(b'Book is successfully added to library!', response.data)

        # Check if the book is displayed in the books route
        response = self.app.get('/books')
        self.assertIn(b'Test Book', response.data)

    def test_loan_and_return_book(self):
        self.login('testuser', 'testpassword')
        test_book = self.create_test_book()

        # Loan the test book
        response = self.app.post('/loan_book', data=dict(
            book_id=test_book.book_id
        ), follow_redirects=True)
        self.assertIn(b'Book successfully loaned!', response.data)

        # Check if the loan is displayed in the loans route
        response = self.app.get('/loans')
        self.assertIn(b'Test Book', response.data)

        # Return the test book
        response = self.app.post('/return_book', data=dict(
            book_id=test_book.book_id
        ), follow_redirects=True)
        self.assertIn(b'Book successfully returned!', response.data)

    def test_customer_details(self):
        self.login('testuser', 'testpassword')
        test_customer = Customer(name='Test User', city='Test City', age=25)
        db.session.add(test_customer)
        db.session.commit()

        response = self.app.post('/customer_detail', data=dict(
            customer_name='Test User'
        ), follow_redirects=True)
        self.assertIn(b'Test User', response.data)

    def test_book_details(self):
        self.login('testuser', 'testpassword')
        test_book = self.create_test_book()

        response = self.app.post('/book_details', data=dict(
            book_name='Test Book'
        ), follow_redirects=True)
        self.assertIn(b'Test Book', response.data)

if __name__ == '__main__':
    unittest.main()
