from flask import Flask, render_template,request, redirect, session, flash
# TODO: Flash message config & Session setup
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from datetime import datetime
import json, requests, os

with open('config.json', 'r') as c:
    jsondata = json.load(c)["jsondata"]


app = Flask(__name__)

app.secret_key = 'f9bf78b9a18ce6d46a0cd2b0b86df9da'
app.config['UPLOAD_FOLDER'] = jsondata['upload_location']
app.config['SQLALCHEMY_DATABASE_URI'] = jsondata['databaseUri']
db = SQLAlchemy(app)



class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Blogposts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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



class Adminlogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    lastlogin = db.Column(db.String(12), nullable=True)



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
        entry = Contact(name=name, phone=phone, message=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        flash("Thank you for contacting us – we will get back to you soon!", "success")
    return render_template('contact.html', jsondata=jsondata)



@app.route('/newsletter', methods = ['GET', 'POST'])
def newsletter():
    if (request.method == 'POST'):
        email = request.form.get('email')
        # ip_address = "8.8.8.8";
        # TODO: Comment above line when website is live on web
        ip_address = request.environ['HTTP_X_FORWARDED_FOR']
        # ip_address = "XX.XXX.XXX.XX"
        url = requests.get("http://ip-api.com/json/{}".format(ip_address))
        j = url.json()
        city = j["city"]
        country =j["country"]
        entry = Newsletter(city=city, country=country, ip=ip_address, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        flash("Newsletter Subscribed Successfully!", "success")
    return redirect('/')

@app.route('/adminlogindetails', methods = ['GET', 'POST'])
def AdminLoginDetails():
    if ('logged_in' in session and session['logged_in'] == True):
        if (request.method == 'POST'):
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password =sha256_crypt.encrypt(request.form.get('password'))
            entry = Adminlogin(name=name, phone=phone, password=password, lastlogin=datetime.now(), email=email)
            db.session.add(entry)
            db.session.commit()
            flash("Admin User Added Successfully!", "success")
        response = Adminlogin.query.order_by(Adminlogin.id).all()
        return render_template('adminlogindetails.html', response=response, jsondata=jsondata)
    else:
        return redirect('/login')

@app.route("/deleteAdminUser/<string:id>", methods = ['GET', 'POST'])
def deleteAdminUser(id):
    if ('logged_in' in session and session['logged_in'] == True):
        deleteAdminUser = Adminlogin.query.filter_by(id=id).first()
        db.session.delete(deleteAdminUser)
        db.session.commit()
        flash("Admin User Deleted Successfully!", "success")
        return redirect('/adminlogindetails')
    else:
        return redirect('/login')

@app.route('/contactresp', methods = ['GET', 'POST'])
def contactResp():
    if ('logged_in' in session and session['logged_in'] == True):
        response = Contact.query.order_by(Contact.id).all()
        return render_template('contactresp.html', response=response, jsondata=jsondata)
    else:
        return redirect('/login')



@app.route("/deleteContact/<string:id>", methods = ['GET', 'POST'])
def deleteContact(id):
    if ('logged_in' in session and session['logged_in'] == True):
        contactResp = Contact.query.filter_by(id=id).first()
        db.session.delete(contactResp)
        db.session.commit()
        flash("Response Deleted Successfully!", "success")
        return redirect('/contactresp')
    else:
        return redirect('/login')



@app.route('/newsletterresp', methods = ['GET', 'POST'])
def newsletterResp():
    if ('logged_in' in session and session['logged_in'] == True):
        response = Newsletter.query.order_by(Newsletter.id).all()
        return render_template('newsletterresp.html', response=response, jsondata=jsondata)
    else:
        return redirect('/login')



@app.route("/deleteNewsletter/<string:id>", methods = ['GET', 'POST'])
def deleteNewsletter(id):
    if ('logged_in' in session and session['logged_in'] == True):
        deleteNewsletter = Newsletter.query.filter_by(id=id).first()
        db.session.delete(deleteNewsletter)
        db.session.commit()
        flash("Response Deleted Successfully!", "success")
        return redirect('/newsletterresp')
    else:
       return redirect('/login')


@app.route("/post/<string:slug>", methods=['GET'])
def postPage(slug):
    post = Blogposts.query.filter_by(slug=slug).first()
    return render_template('post.html', jsondata=jsondata, post=post)

@app.route("/deletePost/<string:id>", methods = ['GET', 'POST'])
def deletePost(id):
    if ('logged_in' in session and session['logged_in'] == True):
        deletePost = Blogposts.query.filter_by(id=id).first()
        db.session.delete(deletePost)
        db.session.commit()
        flash("Post Deleted Successfully!", "success")
        return redirect('/login')
    else:
       return redirect('/login')

@app.route("/edit/<string:id>", methods = ['GET', 'POST'])
def edit(id):
    if ('logged_in' in session and session['logged_in'] == True):
        if request.method == 'POST':
            blog_title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            blog_slug = request.form.get('slug')
            author = request.form.get('author')
            frontimg = request.form.get('frontimg')
            content = request.form.get('editordata')
            timeread = request.form.get('timeread')
            date = datetime.now()
            if id=='0':
                post = Blogposts(title=blog_title,subtitle=subtitle, frontimg=frontimg ,slug=blog_slug, content=content, author=author, timeread=timeread, date=date)
                db.session.add(post)
                db.session.commit()
                flash("Post added Successfully!", "success")
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
                return redirect('/edit/'+id)
        post = Blogposts.query.filter_by(id=id).first()
        return render_template('edit.html', jsondata=jsondata, post=post, id=id)
    return redirect('/login')


@app.route('/login', methods = ['GET', 'POST'])
def loginPage():
    # TODO: Check for active session
    if ('logged_in' in session and session['logged_in'] == True):
        response = Blogposts.query.filter_by().all()
        return render_template('dashboard.html', jsondata=jsondata, response=response)
    if (request.method == 'POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        response = Adminlogin.query.filter_by(email=email).first()
        if((response != None) and ( response.email == email ) and ( sha256_crypt.verify(password, response.password )==1)):
            updateloginTime = Adminlogin.query.filter_by(email=email).first()
            updateloginTime.lastlogin = datetime.now()
            db.session.commit()
            # TODO:Invoke new session
            session['logged_in'] = True
            # TODO: Pull all posts from db and return it
            response = Blogposts.query.filter_by().all()
            return render_template('dashboard.html', jsondata=jsondata, response=response)
        # TODO:Add a invalid login credentials message using flash
        else:
            # if (response == None or (sha256_crypt.verify(password, response.password) != 1)):
            flash("Invalid Credentials!", "danger")
            return render_template('login.html', jsondata=jsondata)
    else:
        return render_template('login.html', jsondata=jsondata)

# TODO: File uploader

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('logged_in' in session and session['logged_in'] == True):
        if (request.method == 'POST'):
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            post = Blogposts.query.all()
            flash("File Uploaded Successfully!", "success")
            return render_template('dashboard.html',jsondata=jsondata,post=post)
    else:
        return redirect('/login')

# TODO: Destroy session ( Logout Function)

@app.route("/logout")
def logout():
    if((session['logged_in'] != True)):
        return redirect('/login')
    else:
        session.pop('logged_in')
        flash("Logged Out Successfully!", "success")
        return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
