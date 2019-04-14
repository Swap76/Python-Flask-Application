from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import os
import psycopg2
from psycopg2.extras import Json, DictCursor
from dotenv import load_dotenv, find_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app=Flask(__name__)

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

@app.route('/')
def house():
	return render_template('house.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/blogs')
def blogs():
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	result = cur.execute('SELECT * FROM blogs')
	blogs = cur.fetchall()

	if blogs:
		return render_template('blogs.html', blogs=blogs)
	else:
		msg = "No Blogs Available!"
		return render_template('blogs.html', msg=msg)

	cur.close()

@app.route('/blog/<string:id>/')
def blog(id):
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	result = cur.execute('SELECT * FROM blogs WHERE id=%s',[id])
	blog = cur.fetchone()

	if blog:
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

		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

		cur.execute('INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)',(name, email, username, password))

		conn.commit()

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
		app.secret_key = 'kittensforever'

		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

		cur.execute('SELECT * FROM users WHERE username=%s',[username])

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

		cur.close()

	return render_template('login.html')	

def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		app.secret_key = 'kittensforever'
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
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	current_user = session['username']
	result = cur.execute('SELECT * FROM blogs WHERE author=%s',[current_user])
	blogs = cur.fetchall()

	if blogs:
		return render_template('dashboard.html', blogs=blogs)
	else:
		msg = "You have no written blogs!"
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

		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

		cur.execute('INSERT INTO blogs(title, body, author) VALUES(%s,%s,%s)',(title, body, session['username']))

		conn.commit()

		cur.close()

		flash('Blog Created!','success')

		return redirect(url_for('dashboard'))

	return render_template('create_blog.html', form=form)


@app.route('/edit_blog/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_blog(id):

	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	result = cur.execute('SELECT * FROM blogs WHERE id=%s',[id])

	blog=cur.fetchone()

	if not blog:
		cur.close()

		flash('No such Blog exists!','danger')
		return redirect(url_for('dashboard'))

	form = BlogForm(request.form)

	form.title.data = blog['title']
	form.body.data = blog['body']

	cur.close()

	if blog['author'] == session['username']:
		if request.method == 'POST' and form.validate():
			title = request.form['title']
			body = request.form['body']

			cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

			cur.execute('UPDATE blogs SET title=%s, body=%s WHERE id=%s',(title, body, id))

			conn.commit()

			cur.close()

			flash('Blog Updated!','success')

			return redirect(url_for('dashboard'))

	else:
		flash('You do not own this Blog!','danger')
		return redirect(url_for('dashboard'))

	return render_template('edit_blog.html', form=form)

@app.route('/delete_blog/<string:id>',methods=['POST'])
@is_logged_in
def delete_blog(id):

	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	result = cur.execute('SELECT * FROM blogs WHERE id=%s',[id])

	blog=cur.fetchone()

	if not blog:
		cur.close()

		flash('No such Blog exists!','danger')
		return redirect(url_for('dashboard'))

	if blog['author'] != session['username']:
		cur.close()

		flash('You don\'t own this Blog!','danger')
		return redirect(url_for('dashboard'))

	result = cur.execute('DELETE FROM blogs WHERE id = %s',[id])
	
	conn.commit()

	cur.close()

	flash('Blog Deleted!','success')
	return redirect(url_for('dashboard'))
		

def create_tables():
	commands = (
		"""
		CREATE TABLE users(
			id SERIAL PRIMARY KEY, 
			name VARCHAR (100) UNIQUE NOT NULL, 
			username VARCHAR (30) UNIQUE NOT NULL, 
			email VARCHAR (50) UNIQUE NOT NULL, 
			password VARCHAR (100) NOT NULL, 
			register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
		""",
		"""
		CREATE TABLE blogs(
			id SERIAL PRIMARY KEY, 
			title VARCHAR (255) UNIQUE NOT NULL, 
			author VARCHAR (100) NOT NULL, 
			body TEXT NOT NULL, 
			create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
		"""
	)
	DATABASE_URL = os.getenv("DATABASE_URL")
	conn = psycopg2.connect(DATABASE_URL, sslmode='require')
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	for command in commands:
		cur.execute(command)
	conn.commit()
	cur.close()

def rollback():
	DATABASE_URL = os.getenv("DATABASE_URL")
	conn = psycopg2.connect(DATABASE_URL, sslmode='require')
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	cur.execute("ROLLBACK")
	conn.commit()
	cur.close()

if __name__=='__main__':
	# create_tables()
	rollback()
	app.secret_key = 'kittensforever'
	app.run(debug=1)