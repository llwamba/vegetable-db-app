# vegetable-db-app

This app is built using flask on the backend, sqlite to store database, and html and css on the front-end.

User can enter the vegetable name and quantity, and the quantity and name will show up on the front-end when added, and data will be stored on the database.

[CLIK HERE TO VIEW DEMO](http://lionelwamba.pythonanywhere.com/)

# DEVELOPMENT CYCLE:

The HTML code defines the user interface for the program. The form elements are used to submit data to the Python program. The Python program uses the flask module to handle the HTTP requests. The program also uses the sqlite3 module to connect to the database. The program uses the cursor object to execute SQL statements.

The program first creates the vegetables table in the database. The program then inserts data into the table. The program then retrieves data from the table. The program then renders the data in the HTML template. The program then displays the data in the browser.

The program is designed to prevent SQL injection. The program only allows data to be inserted into the database. The program allows data to be displayed in the HTML template.

The program is designed to start only when ran. The program is not imported into another program. 
