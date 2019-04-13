### Dependencies

- Python
- Python-Flask
- Flask-WTForms
- Flask-Jinja
- MySQL
- HTML
- BootStrap
- CKEditor 


### Commands used

- install python > 3.3
- install pip
- pip install flask
- sudo apt-get install mysql-server libmysqlclient-dev
- pip install flask-mysqldb
- pip install Flask-WTF
- pip install passlib

mysql:
- mysql -u root -p
- grant all privileges on *.* to root@localhost identified by 'mypassword' with grant option;


### RUN
- python app.py

### SQL Database
- CREATE DATABASE BlogBook;
- USE BlogBook;
- CREATE TABLE users(id INT(11) AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), username VARCHAR(30), email VARCHAR(50), password VARCHAR(100), register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
- CREATE TABLE blogs(id INT(11) AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), author VARCHAR(100), body TEXT, create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);