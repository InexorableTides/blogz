from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import cgi

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    entry = db.Column(db.String(5000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    

    def __init__(self, title, entry, owner):
        self.title = title
        self.entry = entry
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'list_blogs', 'index', 'register']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect('/login')

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', title='User List', users=users)

@app.route('/blog', methods=['POST', 'GET'])
def list_blogs():
    if request.args:
        user = request.args.get('user')
        blogs = Blog.query.filter_by(owner_id=user).all()
        return render_template('blog.html', title='Blogz Fam', blogs=blogs)
    else:
        blogs = Blog.query.all()
        return render_template('blog.html', title="Blogz Fam", blogs=blogs)

@app.route('/add', methods=['POST', 'GET'])
def add_blog():

    if request.method == 'POST':
        blog_name = request.form['blog_title']
        blog_body = request.form['blog_entry']
        owner = User.query.filter_by(email=session['user']).first()
        email = owner.email
        id = owner.id
        error = ''
        
        if len(blog_name) == 0 or len(blog_body) == 0:
            error = "Text is required in both fields."
            return render_template('blog_entry.html', error=error, title='Add Your Blog')

        else:
            new_blog = Blog(blog_name, blog_body, owner)
            db.session.add(new_blog)
            db.session.commit()
            blog_id = new_blog.id
            blog = Blog.query.filter_by(id = blog_id).first()

        return render_template('blog_uno.html', blog_name=blog_name, blog_body=blog_body, title='This is a Blog', email=email, id=id, blog=blog)
    
    return render_template('blog_entry.html', title='Add your Blog')  


@app.route('/blog-post', methods=['POST', 'GET'])
def goto_blog():
    id = request.args.get('id')
    blog = Blog.query.filter_by(id=id).first()
    blog_name = blog.title
    blog_body = blog.entry
    email = blog.owner.email

    return render_template('blog_uno.html', title='This is a Blog', blog_name = blog_name, blog_body = blog_body, email=email, blog=blog)

@app.route("/signup", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        if len(email) < 3 or len(password) < 3:
            flash('Your name is not long enough, fam!')
            return redirect('/signup')
        if not is_email(email):
            flash('Bruh, "' + email + '" is not a real email address')
            return redirect('/signup')
        email_db_count = User.query.filter_by(email=email).count()
        if email_db_count > 0:
            flash('Yo!"' + email + '" is already taken')
            return redirect('/signup')
        if password != verify:
            flash('fam those passwords are not the same')
            return redirect('/signup')
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session['user'] = user.email
        return redirect("/add")
    else:
        return render_template('signup.html')

def is_email(string):
    atsign_index = string.find('@')
    atsign_present = atsign_index >= 0
    if not atsign_present:
        return False
    else:
        domain_dot_index = string.find('.', atsign_index)
        domain_dot_present = domain_dot_index >= 0
        return domain_dot_present

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = User.query.filter_by(email=email)
        if users.count() == 1:
            user = users.first()
            if password == user.password:
                session['user'] = user.email
                flash('Thanks for returning, '+user.email)
                return redirect("/add")
        flash('this is a bad username or password')
        return redirect("/login")

@app.route("/logout", methods=['POST'])
def logout():
    del session['user']
    return redirect("/blog")

app.secret_key = 'itsasecretyo'

if __name__ == '__main__':
app.run()