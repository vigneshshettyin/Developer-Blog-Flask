from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from slugify import slugify
from datetime import datetime
from decouple import config
import json
import requests
import os
import pytz

with open('config.json', 'r') as c:
    jsondata = json.load(c)["jsondata"]

app = Flask(__name__)

app.secret_key = '&^98779843798qbnkj(*&*&(23-VIGNESH-BLOG-SITE-&^*&^*&^hjbv3773h'
app.config['UPLOAD_FOLDER'] = jsondata['upload_location']
app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URI')
db = SQLAlchemy(app)


# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=config('GOOGLE_CLIENT_ID'),
    client_secret=config('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    # This is only needed if using openId to fetch user info
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)


login_manager = LoginManager(app)
login_manager.login_view = 'loginPage'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    google_id = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(50), nullable=True)
    lastlogin = db.Column(db.String(50), nullable=True)
    is_staff = db.Column(db.Integer, nullable=True)
    blogpost = db.relationship(
        'Blogposts', cascade="all,delete", backref='blogpost')


class Blogposts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    slug = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    timeread = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    frontimg = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(80), nullable=False)
    country = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(12), nullable=True)


IST = pytz.timezone('Asia/Kolkata')
x = datetime.now(IST)
time = x.strftime("%c")


@app.route('/')
def homePage():
    post = Blogposts.query.filter_by().all()
    return render_template('index.html', jsondata=jsondata, post=post)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone=phone,
                        message=message, date=time, email=email)
        db.session.add(entry)
        db.session.commit()
        flash("Thank you for contacting us – we will get back to you soon!", "success")
    return render_template('contact.html', jsondata=jsondata)


@app.route('/newsletter', methods=['GET', 'POST'])
def newsletter():
    if (request.method == 'POST'):
        email = request.form.get('email')
        response = Newsletter.query.filter_by(email=email).first()
        if(response == None):
            # ip_address = request.environ['HTTP_X_FORWARDED_FOR']
            ip_address = "43.247.157.20"
            url = requests.get("http://ip-api.com/json/{}".format(ip_address))
            j = url.json()
            city = j["city"]
            country = j["country"]
            entry = Newsletter(city=city, country=country,
                               ip=ip_address, date=time, email=email)
            db.session.add(entry)
            db.session.commit()
            flash("Newsletter subscribed successfully!", "success")
        else:
            flash("Newsletter already subscribed!", "danger")
    return redirect('/')


@app.route('/adminlogindetails', methods=['GET', 'POST'])
@login_required
def AdminLoginDetails():
    if (current_user.is_staff == 1):
        response = User.query.order_by(User.id).all()
        return render_template('adminlogindetails.html', response=response, jsondata=jsondata)
    else:
        flash("No vaild permissions!", "danger")
        return redirect(url_for('dashboard'))


@app.route('/register', methods=['GET', 'POST'])
def RegisterPage():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        password = sha256_crypt.hash(request.form.get('password'))
        entry = User(name=name, password=password,
                     lastlogin=time, email=email, is_staff=0)
        db.session.add(entry)
        db.session.commit()
        flash("User Added Successfully, Now Login", "success")
        return redirect(url_for('loginPage'))
    return render_template('register.html', jsondata=jsondata)


@app.route("/deleteAdminUser/<string:id>", methods=['GET', 'POST'])
@login_required
def deleteAdminUser(id):
    deleteAdminUser = User.query.filter_by(id=id).first()
    if(deleteAdminUser.is_staff == 1):
        flash("Administrator account can't be deleted!", "danger")
    else:
        db.session.delete(deleteAdminUser)
        db.session.commit()
        flash("User deleted successfully!", "success")
    return redirect('/adminlogindetails')


@app.route('/contactresp', methods=['GET', 'POST'])
@login_required
def contactResp():
    if (current_user.is_staff == 1):
        response = Contact.query.order_by(Contact.id).all()
        return render_template('contactresp.html', response=response, jsondata=jsondata)
    else:
        flash("No vaild permissions!", "danger")
        return redirect(url_for('dashboard'))


@app.route("/deleteContact/<string:id>", methods=['GET', 'POST'])
@login_required
def deleteContact(id):
    contactResp = Contact.query.filter_by(id=id).first()
    db.session.delete(contactResp)
    db.session.commit()
    flash("Response deleted successfully!", "success")
    return redirect('/contactresp')


@app.route('/newsletterresp', methods=['GET', 'POST'])
@login_required
def newsletterResp():
    if(current_user.is_staff == 1):
        response = Newsletter.query.order_by(Newsletter.id).all()
        return render_template('newsletterresp.html', response=response, jsondata=jsondata)
    else:
        flash("No vaild permissions!", "danger")
        return redirect(url_for('dashboard'))


@app.route("/deleteNewsletter/<string:id>", methods=['GET', 'POST'])
@login_required
def deleteNewsletter(id):
    deleteNewsletter = Newsletter.query.filter_by(id=id).first()
    db.session.delete(deleteNewsletter)
    db.session.commit()
    flash("Response deleted successfully!", "success")
    return redirect('/newsletterresp')


@app.route("/post/<string:slug>", methods=['GET'])
def postPage(slug):
    post = Blogposts.query.filter_by(slug=slug).first()
    if(post == None):
        return redirect(url_for('homePage'))
    else:
        return render_template('post.html', jsondata=jsondata, post=post)


@app.route("/deletePost/<string:id>", methods=['GET', 'POST'])
@login_required
def deletePost(id):
    deletePost = Blogposts.query.filter_by(id=id).first()
    db.session.delete(deletePost)
    db.session.commit()
    flash("Post deleted successfully!", "success")
    return redirect('/login')


@app.route("/edit/<string:id>", methods=['GET', 'POST'])
@login_required
def edit(id):
    if request.method == 'POST':
        blog_title = request.form.get('title')
        blog_slug = slugify(blog_title)
        frontimg = request.form.get('frontimg')
        content = request.form.get('editordata')
        timeread = request.form.get('timeread')
        date = time
        if id == '0':
            post = Blogposts(title=blog_title, user_id=current_user.id, frontimg=frontimg,
                             slug=blog_slug, content=content, author=current_user.name, timeread=timeread, date=date)
            db.session.add(post)
            db.session.commit()
            flash("Post added successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            post = Blogposts.query.filter_by(id=id).first()
            post.title = blog_title
            post.timeread = timeread
            post.frontimg = frontimg
            post.content = content
            post.date = date
            db.session.commit()
            flash("Post edited Successfully!", "success")
            return redirect(url_for('dashboard'))
    post = Blogposts.query.filter_by(id=id).first()
    return render_template('edit.html', jsondata=jsondata, post=post, id=id)


@app.route('/login', methods=['GET', 'POST'])
def loginPage():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if (request.method == 'POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        response = User.query.filter_by(email=email).first()
        if((response != None) and (response.email == email) and (sha256_crypt.verify(password, response.password) == 1)):
            updateloginTime = User.query.filter_by(email=email).first()
            updateloginTime.lastlogin = time
            db.session.commit()
            login_user(response, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "danger")
            return render_template('login.html', jsondata=jsondata)
    return render_template('login.html', jsondata=jsondata)


@app.route('/authorize/google', methods=['GET', 'POST'])
def Google_loginPage():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    # Access token from google (needed to get user info)
    token = google.authorize_access_token()
    # userinfo contains stuff u specificed in the scrope
    resp = google.get('userinfo')
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    session['profile'] = user_info
    # make the session permanant so it keeps existing after broweser gets closed
    session.permanent = True
    google_id = session['profile']['id']
    response = User.query.filter_by(google_id=google_id).first()
    if(response == None and (User.query.filter_by(email=session['profile']['email']).first()==None)):
        print("Ses-3")
        entry = User(name=session['profile']['name'], password=None,
                     lastlogin=time, email=session['profile']['email'], is_staff=0, google_id=session['profile']['id'])
        db.session.add(entry)
        db.session.commit()
        response = User.query.filter_by(google_id=google_id).first()
        login_user(response)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))
    elif(User.query.filter_by(email=session['profile']['email']).first()!=None):
        print("Ses-1")
        response = User.query.filter_by(email=session['profile']['email']).first()
        response.google_id=session['profile']['id']
        response.lastlogin = time
        db.session.commit()
        login_user(response)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))
    else:
        print("Ses-2")
        response.lastlogin = time
        db.session.commit()
        login_user(response)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if (current_user.is_staff == 1):
        response = Blogposts.query.order_by(Blogposts.id).all()
        return render_template('dashboard.html', jsondata=jsondata, response=response)
    else:
        response = Blogposts.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', jsondata=jsondata, response=response)


@app.route("/uploader", methods=['GET', 'POST'])
@login_required
def uploader():
    if (request.method == 'POST'):
        f = request.files['file1']
        f.save(os.path.join(
            app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        flash("File uploaded successfully!", "success")
        return redirect(url_for('dashboard'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    for key in list(session.keys()):
        session.pop(key)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('loginPage'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=config('DEBUG', default=False, cast=bool))
