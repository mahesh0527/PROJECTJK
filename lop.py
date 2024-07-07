from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, login_required, LoginManager, logout_user, current_user, UserMixin
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/jkstore'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    __tablename__ = 'signup'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

    def get_id(self):
        return str(self.sno)

class Product(db.Model):
    __tablename__ = 'products_details_new'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    main_category = db.Column(db.String(255), nullable=False)
    sub_category = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    link = db.Column(db.String(255), nullable=True)
    ratings = db.Column(db.Float, nullable=True)
    no_of_ratings = db.Column(db.Integer, nullable=True)
    discount_price = db.Column(db.Float, nullable=True)
    actual_price = db.Column(db.Float, nullable=True)

categories = [
    "accessories", "appliances", "bags & luggage", "beauty & health",
    "car & motorbike", "grocery & gourmet foods", "home & kitchen",
    "home, kitchen, pets", "industrial supplies", "kids' fashion",
    "men's clothing", "men's shoes", "music", "pet supplies",
    "sports & fitness", "stores", "toys & baby products",
    "tv, audio & cameras", "women's clothing", "women's shoes"
]

class dabba(db.Model):
    __tablename__ = 'bucket'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('signup.sno'), nullable = False)
    product_id = db.Column(db.Integer, nullable = False)
    quantity = db.Column(db.Integer, nullable = False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name_fun = request.form.get('name')
        user_name_fun = request.form.get('user_name')
        email_fun = request.form.get('Email')
        password_fun = request.form.get('password')

        if not name_fun or not user_name_fun or not email_fun or not password_fun:
            flash('All fields are required.', 'danger')
            return redirect(request.url)

        existing_user = User.query.filter_by(username=user_name_fun).first()
        if existing_user:
            flash('Username already taken. Please choose a different one.', 'danger')
            return render_template('signup.html')

        existing_email = User.query.filter_by(email=email_fun).first()
        if existing_email:
            flash('Email already registered. Please use a different one.', 'danger')
            return render_template('signup.html')

        entry = User(name=name_fun, username=user_name_fun, email=email_fun, password=password_fun)
        db.session.add(entry)
        db.session.commit()
        flash('Signup successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        user = User.query.filter_by(username=user_name).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def productpage(product_id):
    product = Product.query.get_or_404(product_id)
    recommendations = Product.query.filter_by(sub_category=product.sub_category).all()
    random.shuffle(recommendations)
    recommendations = recommendations[:6]
    if request.method == 'POST':
         if 'add_to_cart' in request.form:
            if current_user.is_authenticated:   
                existinng_product=dabba.query.filter_by(product_id=product.id).first()
                ut = request.form.get('quantity')
                if existinng_product:
                    existinng_product.quantity=ut
                    db.session.commit()
                    return redirect(url_for('productpage',product_id=product.id))
                cart_item = dabba(user_id = current_user.sno, product_id = product.id, quantity = ut)
                db.session.add(cart_item)
                db.session.commit()
    return render_template('productpage.html', product=product, recommendations=recommendations)

@app.route('/category/<string:category_name>')
def category_page(category_name):
    # Fetch products belonging to the category
    products = Product.query.filter_by(main_category=category_name).all()
    return render_template('category.html', category_name=category_name, products=products)

@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    if request.method == 'POST':
        delete_item_id = request.form.get('delete_item_id')
        if delete_item_id:
            cart_item = dabba.query.filter_by(user_id=current_user.sno, product_id=delete_item_id).first()
            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
                flash('Item removed from cart.', 'success')
            else:
                flash('Item not found in cart.', 'danger')
                
    cart_items = db.session.query(Product, dabba).join(dabba,Product.id == dabba.product_id ).filter(dabba.user_id == current_user.sno).all()
    return render_template('cart.html', cart_items = cart_items)

@app.route('/')
def home():
    Electronics = Product.query.filter_by(sub_category='All Electronics').all()
    Gaming = Product.query.filter_by(sub_category='Air Conditioners').all()
    Gold = Product.query.filter_by(sub_category='Beauty & Grooming').all()
    Decor = Product.query.filter_by(sub_category="All Home & Kitchen").all()

    random.shuffle(Electronics)
    random.shuffle(Gaming)
    random.shuffle(Gold)
    random.shuffle(Decor)

    Electronics = Electronics[:4]
    Gaming = Gaming[:4]
    Gold = Gold[:4]
    Decor = Decor[:4]

    user_name = current_user.username if current_user.is_authenticated else None

    return render_template('home.html', Ele=Electronics, Gam=Gaming, Gold=Gold, Dcor=Decor, user_name=user_name, categories=categories)


@app.route('/search_suggestions')
def search_suggestions():
    query = request.args.get('q')
    if query:
        suggestions = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
    else:
        suggestions = []
    suggestions_list = [{'id': product.id, 'name': product.name} for product in suggestions]
    return jsonify(suggestions_list)

if __name__ == '__main__':
    app.run(debug=True)