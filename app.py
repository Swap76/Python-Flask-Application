from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app=Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'kittensforever'
app.config['MYSQL_DB'] = 'BlogBook'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def house():
	return render_template('house.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/blogs')
def blogs():
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM blogs")
	blogs = cur.fetchall()

	if result > 0:
		return render_template('blogs.html', blogs=blogs)
	else:
		msg = "No Blogs Available!"
		return render_template('blogs.html', msg=msg)

	cur.close()

@app.route('/blog/<string:id>/')
def blog(id):
	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM blogs WHERE id=%s",[id])

	if result > 0:
		blog = cur.fetchone()
		return render_template('blog.html', blog=blog)
	else:
		flash('No such Blog!','danger')
		return redirect(url_for('blogs'))

	cur.close()


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

		cur.close()

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
	cur = mysql.connection.cursor()
	current_user = session['username']
	result = cur.execute("SELECT * FROM blogs WHERE author=%s",[current_user])
	blogs = cur.fetchall()

	if result > 0:
		return render_template('dashboard.html', blogs=blogs)
	else:
		msg = "You haven't written any blogs yet!"
		return render_template('dashboard.html', msg=msg)

	cur.close()

class BlogForm(Form):
	title = StringField('Title',[validators.DataRequired(), validators.Length(min=1,max=250)])
	body = TextAreaField('Body',[validators.DataRequired(), validators.Length(min=5)])

@app.route('/create_blog',methods=['GET','POST'])
@is_logged_in
def create_blog():
	form = BlogForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		cur = mysql.connection.cursor()

		cur.execute("INSERT INTO blogs(title, body, author) VALUES(%s,%s,%s)",(title, body, session['username']))

		mysql.connection.commit()

		cur.close()

		flash('Blog Created!','success')

		return redirect(url_for('dashboard'))

	return render_template('create_blog.html', form=form)


@app.route('/edit_blog/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_blog(id):

	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM blogs WHERE id=%s",[id])

	if result <= 0:
		cur.close()
		flash('No such Blog exists!','danger')
		return redirect(url_for('dashboard'))

	blog=cur.fetchone()


	form = BlogForm(request.form)

	form.title.data = blog['title']
	form.body.data = blog['body']

	cur.close()

	if blog['author'] == session['username']:
		if request.method == 'POST' and form.validate():
			title = request.form['title']
			body = request.form['body']

			cur = mysql.connection.cursor()

			cur.execute("UPDATE blogs SET title=%s, body=%s WHERE id=%s",(title, body, id))

			mysql.connection.commit()

			cur.close()

			flash('Blog Updated!','success')

			return redirect(url_for('dashboard'))

	else:
		flash('You do not own this Blog!','danger')
		return redirect(url_for('dashboard'))

	return render_template('edit_blog.html', form=form)


if __name__=='__main__':
	app.secret_key = 'kittensforever'
	app.run(debug=1)