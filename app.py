from flask import Flask, render_template,request, redirect, session, flash, url_for
# TODO: Flash message config & Session setup
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from datetime import datetime
import json, requests, os

with open('config.json', 'r') as c:
    jsondata = json.load(c)["jsondata"]


app = Flask(__name__)

app.secret_key = '&^98779843798qbnkj(*&*&(23-VIGNESH-BLOG-SITE-&^*&^*&^hjbv3773h'
app.config['UPLOAD_FOLDER'] = jsondata['upload_location']
app.config['SQLALCHEMY_DATABASE_URI'] = jsondata['databaseUri']
db = SQLAlchemy(app)

#use LoginManager to provide login functionality and do some initial confg
login_manager = LoginManager(app)
login_manager.login_view = 'loginPage'
login_manager.login_message_category = 'info'

#function to load the currently active user
@login_manager.user_loader
def load_user(user_id):
    return Adminlogin.query.get(user_id)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Adminlogin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    lastlogin = db.Column(db.String(12), nullable=True)
    blogpost = db.relationship('Blogposts', cascade="all,delete", backref='blogpost')

class Blogposts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('adminlogin.id'))
    slug = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    timeread = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    subtitle = db.Column(db.String(150), nullable=False)
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

x = datetime.now()
time = x.strftime("%c")

@app.route('/')
def homePage():
    post = Blogposts.query.filter_by().all()
    return render_template('index.html', jsondata=jsondata, post=post)



@app.route('/about')
def about():
    return render_template('about.html', jsondata=jsondata)



@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone=phone, message=message, date=time, email=email)
        db.session.add(entry)
        db.session.commit()
        flash("Thank you for contacting us – we will get back to you soon!", "success")
    return render_template('contact.html', jsondata=jsondata)



@app.route('/newsletter', methods = ['GET', 'POST'])
def newsletter():
    if (request.method == 'POST'):
        email = request.form.get('email')
        # TODO: Comment above line when website is live on web
        # ip_address = request.environ['HTTP_X_FORWARDED_FOR']
        ip_address = "43.247.157.20";
        url = requests.get("http://ip-api.com/json/{}".format(ip_address))
        j = url.json()
        city = j["city"]
        country =j["country"]
        entry = Newsletter(city=city, country=country, ip=ip_address, date=time, email=email)
        db.session.add(entry)
        db.session.commit()
        flash("Newsletter Subscribed Successfully!", "success")
    return redirect('/')

# @app.route('/test', methods = ['GET', 'POST'])
# def test():
#     name = "Vignesh"
#     email = "vigneshshetty.in@gmail.com"
#     phone = "6362490109"
#     password ="admin"
#     password = sha256_crypt.hash(password)
#     entry = Adminlogin(name=name, phone=phone, password=password, lastlogin=time, email=email)
#     db.session.add(entry)
#     db.session.commit()
#     return redirect(url_for('loginPage'))

@app.route('/adminlogindetails', methods = ['GET', 'POST'])
@login_required
def AdminLoginDetails():
    if (current_user.email == jsondata["adminemail"]):
        response = Adminlogin.query.order_by(Adminlogin.id).all()
        return render_template('adminlogindetails.html', response=response, jsondata=jsondata)
    else:
        flash("No vaild permissions!", "danger")
        return redirect(url_for('dashboard'))


@app.route('/register', methods = ['GET', 'POST'])
def RegisterPage():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = sha256_crypt.hash(request.form.get('password'))
        entry = Adminlogin(name=name, phone=phone, password=password, lastlogin=time, email=email)
        db.session.add(entry)
        db.session.commit()
        flash("User Added Successfully, Now Login", "success")
    return render_template('register.html',jsondata=jsondata)

@app.route("/deleteAdminUser/<string:id>", methods = ['GET', 'POST'])
@login_required
def deleteAdminUser(id):
        deleteAdminUser = Adminlogin.query.filter_by(id=id).first()
        if(deleteAdminUser.email==jsondata["adminemail"]):
            flash("Administrator account can't be deleted!", "danger")
        else:
            db.session.delete(deleteAdminUser)
            db.session.commit()
            flash("User deleted successfully!", "success")
        return redirect('/adminlogindetails')

@app.route('/contactresp', methods = ['GET', 'POST'])
@login_required
def contactResp():
    if (current_user.email == jsondata["adminemail"]):
        response = Contact.query.order_by(Contact.id).all()
        return render_template('contactresp.html', response=response, jsondata=jsondata)
    else:
        flash("No vaild permissions!", "danger")
        return redirect(url_for('dashboard'))



@app.route("/deleteContact/<string:id>", methods = ['GET', 'POST'])
@login_required
def deleteContact(id):
        contactResp = Contact.query.filter_by(id=id).first()
        db.session.delete(contactResp)
        db.session.commit()
        flash("Response deleted successfully!", "success")
        return redirect('/contactresp')



@app.route('/newsletterresp', methods = ['GET', 'POST'])
@login_required
def newsletterResp():
        if(current_user.email==jsondata["adminemail"]):
            response = Newsletter.query.order_by(Newsletter.id).all()
            return render_template('newsletterresp.html', response=response, jsondata=jsondata)
        else:
            flash("No vaild permissions!", "danger")
            return redirect(url_for('dashboard'))



@app.route("/deleteNewsletter/<string:id>", methods = ['GET', 'POST'])
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
    return render_template('post.html', jsondata=jsondata, post=post)

@app.route("/deletePost/<string:id>", methods = ['GET', 'POST'])
@login_required
def deletePost(id):
        deletePost = Blogposts.query.filter_by(id=id).first()
        db.session.delete(deletePost)
        db.session.commit()
        flash("Post deleted successfully!", "success")
        return redirect('/login')

@app.route("/edit/<string:id>", methods = ['GET', 'POST'])
@login_required
def edit(id):
        if request.method == 'POST':
            blog_title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            blog_slug = request.form.get('slug')
            author = request.form.get('author')
            frontimg = request.form.get('frontimg')
            content = request.form.get('editordata')
            timeread = request.form.get('timeread')
            date = time
            if id=='0':
                post = Blogposts(title=blog_title,user_id=current_user.id, subtitle=subtitle, frontimg=frontimg ,slug=blog_slug, content=content, author=author, timeread=timeread, date=date)
                db.session.add(post)
                db.session.commit()
                flash("Post added successfully!", "success")
                return redirect(url_for('dashboard'))
            else:
                post = Blogposts.query.filter_by(id=id).first()
                post.title = blog_title
                post.subtitle= subtitle
                post.slug = blog_slug
                post.timeread = timeread
                post.frontimg = frontimg
                post.content = content
                post.author = author
                post.date = date
                db.session.commit()
                flash("Post edited Successfully!", "success")
                # return redirect('/edit/'+id)
                return redirect(url_for('dashboard'))
        post = Blogposts.query.filter_by(id=id).first()
        return render_template('edit.html', jsondata=jsondata, post=post, id=id)


@app.route('/login', methods = ['GET', 'POST'])
def loginPage():
    # TODO: Check for active session
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if (request.method == 'POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        response = Adminlogin.query.filter_by(email=email).first()
        if((response != None) and ( response.email == email ) and ( sha256_crypt.verify(password, response.password )==1)):
            updateloginTime = Adminlogin.query.filter_by(email=email).first()
            updateloginTime.lastlogin = time
            db.session.commit()
            # TODO:Invoke new session
            # log the user in using login_user
            login_user(response, remember=remember)
            # go to the page that the user tried to access if exists
            # otherwise go to the dash page
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            # TODO: Pull all posts from db and return it
            response = Blogposts.query.filter_by().all()
            return render_template('dashboard.html', jsondata=jsondata, response=response)
        # TODO:Add a invalid login credentials message using flash
        else:
            # if (response == None or (sha256_crypt.verify(password, response.password) != 1)):
            flash("Invalid credentials!", "danger")
            return render_template('login.html', jsondata=jsondata)
    return render_template('login.html', jsondata=jsondata)
# TODO: File uploader

@app.route('/dashboard', methods = ['GET', 'POST'])
@login_required
def dashboard():
    if (current_user.email == jsondata["adminemail"]):
        response = Blogposts.query.order_by(Blogposts.id).all()
        return render_template('dashboard.html', jsondata=jsondata, response=response)
    else:
        response = Blogposts.query.filter_by(user_id = current_user.id).all()
        return render_template('dashboard.html', jsondata=jsondata, response=response)

@app.route("/uploader", methods = ['GET', 'POST'])
@login_required
def uploader():
        if (request.method == 'POST'):
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            post = Blogposts.query.all()
            flash("File uploaded successfully!", "success")
            return redirect(url_for('dashboard'))

# TODO: Destroy session ( Logout Function)

@app.route('/logout')
@login_required
def logout():
    #log the user out using logout_user, flash a msg and go to the login page
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('loginPage'))

if __name__ == '__main__':
    app.run(debug=True)
