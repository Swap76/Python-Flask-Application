from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from data import Blogs
from functools import wraps

app=Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'kittensforever'
app.config['MYSQL_DB'] = 'BlogBook'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

Blogs = Blogs()

@app.route('/')
def house():
	return render_template('house.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/blogs')
def blogs():
	return render_template('blogs.html',blogs = Blogs)

@app.route('/blog/<string:id>/')
def blog(id):
	return render_template('blog.html',blogs = Blogs,id=int(id))

class RegisterForm(Form):
	name = StringField('Name',[validators.DataRequired(), validators.Length(min=1,max=50)])
	email = StringField('Email',[validators.DataRequired(), validators.Length(min=5,max=50)])
	username = StringField('Username',[validators.DataRequired(), validators.Length(min=5,max=20)])
	password = PasswordField('Password',[validators.DataRequired(), validators.Length(min=5,max=50), validators.EqualTo('confirm',message="Passwords do not match!")])
	confirm = PasswordField('Confirm Password')

def is_logged_out(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			flash('You are already logged in!','danger')
			return redirect(url_for('house'))
		else:
			return f(*args, **kwargs)
	return wrap

@app.route('/register',methods=['GET','POST'])
@is_logged_out
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name=form.name.data
		email=form.email.data
		username=form.username.data
		password=sha256_crypt.encrypt(str(form.password.data))

		cur=mysql.connection.cursor()

		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",(name, email, username, password))

		mysql.connection.commit()

		cur.close()

		flash('You are now registered with The BlogBook!','success')

		return redirect(url_for('login'))

	return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
@is_logged_out
def login():
	if request.method == 'POST':
		username=request.form['username']
		password_tried=request.form['password']

		cur = mysql.connection.cursor()

		result = cur.execute("SELECT * FROM users WHERE username=%s",[username])

		if result > 0:
			data = cur.fetchone()
			password = data['password']

			if sha256_crypt.verify(password_tried, password):
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in and ready to write blogs!','success')
				return redirect(url_for('dashboard'))

			else:
				error = "Password Not Matched"
				return render_template('login.html',error=error)

		else:
			error="No Such User"
			return render_template('login.html',error=error)

	return render_template('login.html')	

def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('You are not authorized, please login!','danger')
			return redirect(url_for('login'))
	return wrap

@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out!','success')
	return redirect(url_for('house'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
	return render_template('dashboard.html')

if __name__=='__main__':
	app.secret_key = 'kittensforever'
	app.run(debug=1)