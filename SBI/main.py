from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os 


with open('config.json', 'r') as fp:
    parameters = json.load(fp)['parameters']
local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = parameters['img_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME=parameters['gmail-user'],
    MAIL_PASSWORD=parameters['gmail-password']
)
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['production_uri']

db = SQLAlchemy(app)


class SBI(db.Model):          # SBI is table name in flask DB (class name and table name in DB must be same)
    account_number = db.Column(db.Integer, primary_key=True)    # column name in table
    full_name = db.Column(db.String(50), nullable=False)        # column name in table
    mobile_number = db.Column(db.Integer, nullable=False)       # column name in table
    email = db.Column(db.String(50), nullable=False)            # column name in table
    massage = db.Column(db.String(50), nullable=False)          # column name in table
    date = db.Column(db.String(50), nullable=False)             # column name in table
    img = db.Column(db.String(50), nullable=False)              # column name in table


@app.route('/')
def home_page():
    return render_template("index.html", parameters=parameters)


@app.route('/about')
def about_me():
    name = 'Nilesh'
    return render_template("about.html", TemplateName=name, parameters=parameters)


@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        acc_number = request.form.get('accountnumber')
        first_name = request.form.get('fname')
        mob_name = request.form.get('mnumber')
        e_mail = request.form.get('email')
        massage = request.form.get('massage')
        date = request.form.get('date')
        img = request.files['img']
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(img.filename)))

        entry = SBI(account_number=acc_number,
                    full_name=first_name,
                    mobile_number=mob_name,
                    email=e_mail,
                    massage=massage,
                    date=date,
                    img=img
                    )                       # class_name(class_variable=function_variable)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + first_name,
                          sender=e_mail,
                          recipients=[parameters['gmail-user']],
                          body="Dear sir/mam"+"\n"+first_name+" is apply for card"+"\n"+mob_name+"\n"+massage
                          )
    return render_template("apply.html", parameters=parameters)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user'] == parameters['admin_user']:
        posts = SBI.query.all()     # className.query.all()
        return render_template("view.html", parameters=parameters, posts=posts)
    if request.method == 'POST':    # redirect to admin panel
        user_name = request.form.get("user_name")
        user_password = request.form.get("password")
        if user_name == parameters['admin_user'] and user_password == parameters['admin-password']:     # set the session variable
            session['user'] = user_name
            posts = SBI.query.all()      # className.query.all()
            return render_template("view.html", parameters=parameters, posts=posts)

    return render_template("login.html", parameters=parameters)


@app.route('/edit/<string:account_number>', methods=['GET', 'POST'])
def edit(account_number):
    if 'user' in session and session['user'] == parameters['admin_user']:
        if request.method == 'POST':
            req_account_number = request.form.get('accountnumber')
            req_first_name = request.form.get('fname')
            req_mob_name = request.form.get('mnumber')
            req_e_mail = request.form.get('email')
            req_massage = request.form.get('massage')
            req_date = request.form.get('date')
            req_img = request.form.get('img')

            if account_number == '0':
                post = SBI(account_number=req_account_number, full_name=req_first_name,
                           mobile_number=req_mob_name, email=req_e_mail, massage=req_massage,
                           date=req_date, img=req_img)
                db.session.add(post)
                db.session.commit()
            else:
                post = SBI.query.filter_by(account_number=account_number).first()
                post.account_number = req_account_number     # class parameter = function edit variables
                post.full_name = req_first_name              # class parameter = function edit variables
                post.mobile_number = req_mob_name            # class parameter = function edit variables
                post.email = req_e_mail                      # class parameter = function edit variables
                post.massage = req_massage                   # class parameter = function edit variables
                post.date = req_date                         # class parameter = function edit variables
                post.img = req_img                           # class parameter = function edit variables
                db.session.commit()
                return redirect('/edit/' + account_number)
        post = SBI.query.filter_by(account_number=account_number).first()
        return render_template('edit.html', parameters=parameters, post=post, account_number=account_number)


@app.route('/delete/<string:account_number>', methods=['GET', 'POST'])
def delete(account_number):
    if "user" in session and session['user'] == parameters['admin_user']:
        post = SBI.query.filter_by(account_number=account_number).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')


app.run(debug=True)
