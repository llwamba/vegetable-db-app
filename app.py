import os
from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from markupsafe import escape
from waitress import serve


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.debug = True

database_uri = os.getenv('DATABASE_URL')
if not database_uri:
    raise EnvironmentError("DATABASE_URL environment variable is not set")

print(f"DATABASE_URL: {database_uri}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

db = SQLAlchemy(app)

migrate = Migrate(app, db)


class Vegetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_value = db.Column(db.Float)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), EqualTo('password')])


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


@app.cli.command("init_db")
def init_db():
    """
    Initialize the database.

    This function is responsible for creating the necessary tables if they don't exist.
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    with app.app_context():
        db.create_all()
        click.echo("Database Initialized")


@app.before_request
def before_request():
    if 'logged_in' in session:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')


def valid_login(username, password):
    user = User.query.filter_by(name=escape(username)).first()
    if user and check_password_hash(escape(password), password):
        return True
    return False


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('base.html', title="Vegetable Database App")


@app.route('/add-vegetable', methods=['GET', 'POST'])
def add_vegetable():
    name = ''
    quantity = ''
    price = ''
    valid = False
    total_sum = 0

    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        valid = True
        if not name or not quantity:
            flash('⚠️You must give a name and a quantity for the vegetable!')
            valid = False
        else:
            try:
                quantity = int(quantity)
                price = float(price)
            except ValueError:
                flash('Quantity must be an integer, and price must be a float')
                valid = False

    if valid:
        total_value = quantity * price
        new_vegetable = Vegetable(
            name=escape(name), quantity=quantity, price=price, total_value=total_value)
        db.session.add(new_vegetable)
        db.session.commit()
        flash(
            f'Vegetable {escape(name)} was added with a quantity of {quantity}')

    vegetables = Vegetable.query.all()
    total_sum = db.session.query(db.func.sum(Vegetable.total_value)).scalar()

    return render_template(
        'add_vegetable.html',
        title="Vegetable Database App",
        vegetables=vegetables,
        name=name,
        quantity=quantity,
        price=price,
        total_sum=total_sum
    )


@app.route('/query', methods=['GET', 'POST'])
def query():
    query_str = ''
    results = []

    if request.method == 'POST':
        query_str = request.form.get('query_str')

        if query_str:
            results = Vegetable.query.filter(
                Vegetable.name.like(f'%{escape(query_str)}%')).all()

    return render_template(
        'query.html',
        title="Query Vegetable",
        results=results,
        query_str=query_str
    )


@app.route('/edit/<int:vegetable_id>', methods=['GET', 'POST'])
def edit_vegetable(vegetable_id):
    vegetable = Vegetable.query.get_or_404(vegetable_id)

    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        valid = True

        if not name or not quantity:
            flash('⚠️ You must provide a name and a quantity for the vegetable!')
            valid = False
        else:
            try:
                quantity = int(quantity)
                price = float(price)
            except ValueError:
                flash('Quantity must be an integer, and price must be a float')
                valid = False

        if valid:
            vegetable.name = escape(name)
            vegetable.quantity = quantity
            vegetable.price = price
            vegetable.total_value = quantity * price
            db.session.commit()
            flash('Vegetable data updated successfully!')
            return redirect(url_for('index'))

    return render_template('edit_vegetable.html', title="Edit Vegetable", vegetable=vegetable)


@app.route('/delete/<int:vegetable_id>', methods=['GET', 'POST'])
def delete_vegetable(vegetable_id):
    vegetable = Vegetable.query.get_or_404(vegetable_id)

    if request.method == 'POST':
        db.session.delete(vegetable)
        db.session.commit()
        flash(
            f'Vegetable {escape(vegetable.name)} has been deleted successfully!', 'success')
        # Redirect to add_vegetable page after deleting
        return redirect(url_for('add_vegetable'))

    return render_template('delete_vegetable.html', title="Delete Vegetable", vegetable=vegetable)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        existing_user = User.query.filter_by(name=escape(username)).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            hashed_password = generate_password_hash(
                escape(password), method='sha256')
            new_user = User(name=escape(username), password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        app.logger.debug(
            f'Attempting login for username: {escape(username)}, password: {escape(password)}')

        if valid_login(username, password):
            session['logged_in'] = True
            session['username'] = username
            app.logger.debug('Logged in successfully!')
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            app.logger.debug('Invalid username or password. Please try again.')
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
