
from flask import Flask, flash, render_template, request, redirect, url_for
import sqlite3
HEADER = '''\
LIONEL LWAMBA
10/06/2022
CRN: 10235
CIS 226: Advanced Python Programming
Estimated time to complete assignment: 2 hours
'''


DB_PATH = 'db.sqlite3'

app = Flask(__name__)
app.secret_key = b'Upg3zhGacjrP4mAf6bDU71GL7p7acQvPHIQknxBte4o'

# Our DB class does not need to know anything about flask or the web


class Vegetables:
    def __init__(self, conn):
        self.conn = conn
        self.c = self.conn.cursor()

    def setup(self):
        self.c.execute(
            "CREATE TABLE IF NOT EXISTS vegetable (quantity INTEGER, name TEXT)")
        self.conn.commit()

    def get_all(self):
        for row in self.c.execute("SELECT * FROM vegetable"):
            yield row

    def add_vegetable(self, name, quantity):
        self.c.execute("INSERT INTO vegetable VALUES (?, ?)", [quantity, name])

    def find_vegetable(self, name):
        self.c.execute("SELECT * FROM vegetable WHERE name=?", [name])
        row = self.c.fetchone()  # Get first row
        return row


def db_setup():
    """Setup the db if needed"""
    app.logger.debug("Setting up db...")
    with sqlite3.connect(DB_PATH) as conn:
        v = Vegetables(conn)
        v.setup()
    app.logger.debug("Setting up db [Done]")


# Create table if needed when app starts
app.before_first_request(db_setup)


@app.route('/', methods=['GET', 'POST'])
def index():
    name = ''
    quantity = ''
    valid = False
    if request.method == 'POST':
        # Validate form
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        valid = True
        if not name or not quantity:
            flash('⚠️You must give a name and a quantity for the vegetable!')
            valid = False
        else:
            try:
                quantity = int(quantity)
            except ValueError:
                flash('quantity must be an integer')
                valid = False

    # Open and close the db within the request
    with sqlite3.connect(DB_PATH) as conn:
        v = Vegetables(conn)
        # Add vegetable if form was valid
        if valid:
            v.add_vegetable(name, quantity)
            flash('Vegetable {} was added with quantity of {}'.format(name, quantity))
            # Always redirect after a POST was valid
            return redirect(url_for('index'))
        # Get new list of vegetables to display
        vegetables = v.get_all()
    return render_template(
        'base.html',
        title="Vegetable Database App",
        vegetables=vegetables,
        name=name,
        quantity=quantity,
    )
