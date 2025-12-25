from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TelField, DateField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Optional
from datetime import datetime
import sqlite3
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_change_me_2025'  # Change this in production!
# App config add (after app = Flask(__name__))
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'anuanu96660@gmail.com'   

app.config['MAIL_PASSWORD'] = 'lvrd rmwg ivvn nvwx'  # App Password
app.config['MAIL_DEFAULT_SENDER'] = 'yourgmail@gmail.com'

mail = Mail(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, async_mode='eventlet')
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, email FROM users WHERE id=?", (user_id,))
    user_data = cur.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

# Forms
class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DonorRegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    blood_group = SelectField('Blood Group', choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = TelField('Phone Number', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    last_donated = DateField('Last Donation Date (optional)', format='%Y-%m-%d', validators=[Optional()])
    lat = FloatField('Latitude', validators=[Optional()])
    lng = FloatField('Longitude', validators=[Optional()])
    submit = SubmitField('Register as Donor')

class SearchForm(FlaskForm):
    blood_group = SelectField('Blood Group', choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'),
        ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    submit = SubmitField('Search Donors')

class EmergencyForm(FlaskForm):
    patient_name = StringField('Patient Name', validators=[DataRequired()])
    blood_group = SelectField('Blood Group', choices=[
        ('', 'Select Blood Group'),
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    contact = TelField('Contact Number', validators=[DataRequired()])
    submit = SubmitField('Request Emergency')

# Availability check
def is_available(last_donated):
    if not last_donated:
        return 1
    try:
        last = datetime.strptime(last_donated, "%Y-%m-%d")
        days = (datetime.now() - last).days
        return 1 if days >= 90 else 0
    except:
        return 1

# Routes
@app.route('/')
def index():
    return render_template("index.html", user=current_user if current_user.is_authenticated else None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                        (form.name.data, form.email.data, hashed_pw))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
        finally:
            conn.close()
    return render_template("register.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (form.email.data,))
        user = cur.fetchone()
        conn.close()
        if user and bcrypt.check_password_hash(user[3], form.password.data):
            user_obj = User(user[0], user[1], user[2])
            login_user(user_obj)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template("login.html", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/donor_register', methods=['GET', 'POST'])
@login_required
def donor_register():
    form = DonorRegisterForm()
    if form.validate_on_submit():
        last_donated_str = form.last_donated.data.strftime("%Y-%m-%d") if form.last_donated.data else None
        available = is_available(last_donated_str)
        data = (
            form.name.data,
            form.blood_group.data,
            form.email.data,
            form.phone.data,
            form.city.data,
            last_donated_str,
            available,
            form.lat.data,
            form.lng.data
        )
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO donor (name, blood_group, email, phone, city, last_donated, available, lat, lng)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, data)
        conn.commit()
        conn.close()
        flash('Donor registered successfully!', 'success')
        return redirect(url_for('index'))
    return render_template("donor_register.html", form=form)


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    donors = None

    if form.validate_on_submit():
        blood = form.blood_group.data
        city = form.city.data
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT name, phone, city, lat, lng
            FROM donor
            WHERE blood_group=? AND city=? AND available=1
        """, (blood, city))
        donors = cur.fetchall()
        conn.close()
        return redirect(url_for('results', blood_group=blood, city=city))
    return render_template("search.html", form=form, donors=donors)


@app.route('/search', methods=['GET'])
@login_required
def search_form():
    form = SearchForm()
    return render_template("search.html", form=form)

@app.route('/results')
@login_required
def results():
    # Get query parameters from URL
    blood_group = request.args.get('blood_group')
    city = request.args.get('city')
    
    # If no parameters (direct access), redirect to search
    if not blood_group or not city:
        flash('Please search for donors first.', 'warning')
        return redirect(url_for('search'))
    
    # Database query - case insensitive + partial city match
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT name, phone, city, lat, lng 
        FROM donor 
        WHERE blood_group = ? 
          AND UPPER(city) LIKE UPPER(?) 
          AND available = 1
    """, (blood_group, f"%{city}%"))
    donors = cur.fetchall()
    conn.close()
    
    return render_template("results.html", donors=donors,blood_group=blood_group,
    city=city)
@app.route('/emergency', methods=['GET', 'POST'])
@login_required
def emergency():
    form = EmergencyForm()
    if form.validate_on_submit():
        data = (
            form.patient_name.data,
            form.blood_group.data,
            form.city.data,
            form.contact.data,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        
        # Step 1: Insert the emergency request
        cur.execute("""
            INSERT INTO emergency (patient_name, blood_group, city, contact, date)
            VALUES (?,?,?,?,?)
        """, data)
        conn.commit()
        
        # Step 2: Find matching donors (BEFORE closing connection!)
        cur.execute("""
            SELECT name, email
            FROM donor
            WHERE blood_group=? AND city=? AND available=1
        """, (form.blood_group.data, form.city.data))
        matching_donors = cur.fetchall()
        
        # Step 3: Send emails to matching donors
        for donor in matching_donors:
            donor_name, donor_email = donor
            if donor_email:  # Skip if no email
                msg = Message(
                    subject="Urgent Blood Request - Blood Donation Finder",
                    recipients=[donor_email],
                    body=f"""
                    Dear {donor_name},

                    There is an urgent request for {form.blood_group.data} blood in {form.city.data}!
                    Patient: {form.patient_name.data}
                    Contact: {form.contact.data}

                    Please contact them immediately if you can donate.

                    Thank you for saving lives!
                    Blood Donation Finder Team
                    """
                )
                mail.send(msg)
        
        conn.close()  # Close ONLY after all operations
        
        socketio.emit('emergency_alert', {
            'message': f'Urgent {form.blood_group.data} blood needed in {form.city.data}! Patient: {form.patient_name.data}'
        })

        flash('Emergency request submitted! Matching donors notified via email.', 'success')
        return redirect(url_for('index'))
    
    return render_template("emergency.html", form=form)    
        
    
@app.route('/admin')
@login_required
def admin():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM donor")
    donors = cur.fetchall()
    cur.execute("SELECT * FROM emergency ORDER BY date DESC")
    emergencies = cur.fetchall()
    conn.close()
    return render_template("admin.html", donors=donors, emergencies=emergencies)

# SocketIO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == "__main__":
    socketio.run(app, debug=True)