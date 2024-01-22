Guy Ankry's Books Library Management System
Welcome to the Books Library Management System!
This library was created to service your needs if you are looking for a book!

This is how its works:

Database Structure
Books Table:

Id (PK): Primary key for each book.
Title: Title of the book.
Author: Author of the book.
Year Published: Year the book was published.
Type (1/2/3): Book type, determining the maximum loan time.
Customers Table:

Id (PK): Primary key for each customer.
Name: Name of the customer.
City: City of residence of the customer.
Age: Age of the customer.
Loans Table:

CustID: Foreign key referencing a customer's Id.
BookID: Foreign key referencing a book's Id.
Loandate: Date when the book was borrowed.
Returndate: Date when the book is expected to be returned.


Maximum Loan Time Based on Book Type, the book type determines the maximum loan time for a book:
Type 1: Up to 10 days
Type 2: Up to 5 days
Type 3: Up to 2 days


DAL Modules:
books: Defines the Books class for book-related operations.
customers: Defines the Customers class for customer-related operations.
loans: Defines the Loans class for loan-related operations.


Client Application
A client application is built to interact with the DAL, allowing users to register and log in with restricted access. Each user has a personal page displaying their loaned books and active loans. The client application provides a menu-driven interface for the following operations:

Add a new customer
Add a new book
Loan a book
Return a book
Display all books
Display all customers
Display all loans
Display late loans
Find book by name


Getting Started:
Create a new project.
Activate the virtual environment.
Install dependencies from requirements.txt.
Run the Flask app: python app.py (MAC: python3 app.py).
Open your browser and navigate to the local address to view the project.


Happy reading! 📚