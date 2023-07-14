
#### snippets HTML CSS, easy to use
#### https://www.bootdey.com/bootstrap-snippets


from flask import Flask, render_template, url_for, redirect, flash, get_flashed_messages, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import now


from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user

from flask_bootstrap import Bootstrap
from forms import RegisterForm, LoginForm, NewProduct

from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


#### DATABASE ACCESS
host = '127.0.0.1'
user = 'PythonUser'
password = 'Python2022%'
database = 'Shopping'
port = 3306

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{user}:{password}@{host}:{port}/{database}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


##### LOGIN Manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # return User.get(user_id)  ### According to flask login web page
    # print("User Loader con query ", User.query.filter_by(id=user_id).first())
    # print("User Loader con query TYpe", type(User.query.filter_by(id=user_id).first()))
    # return User.query.filter_by(id=user_id).first()


    ### BOTH Options works fine, I keep this one since the query is depricated and sometime gets errors
    # print("LOad USER", db.session.execute(db.select(User).filter_by(id=user_id)).first()[0])
    # print("LOad USER Type", type(db.session.execute(db.select(User).filter_by(id=user_id)).first()))
    return db.session.execute(db.select(User).filter_by(id=user_id)).first()[0]


###### DBs

class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(250))
    name = db.Column(db.String(250))

    ### relation with the other table
    sales_user = relationship('Sales', back_populates='owner')



##### Table products for sale
class Products(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True)
    description = db.Column(db.String(250))
    price = db.Column(db.Float())
    photo = db.Column(db.String(250))




#### Table for efective sales
class Sales(db.Model):
    __tablename__ = 'Sales'
    id = db.Column(db.Integer, primary_key=True)
    product_id_sold = db.Column(db.Integer())
    product_id_name = db.Column(db.String(250))
    price_sold = db.Column(db.Integer())
    buyer = db.Column(db.Integer, db.ForeignKey('User.id'))  ### Foreing key
    sold_at = db.Column(db.DateTime(), server_default=now())

    ### relation with the User Table
    owner = relationship('User', back_populates='sales_user')

### create the tables if doesn't exist
with app.app_context():
    db.create_all()



@app.route("/login", methods=['GET', 'POST'])
def login():

    form_login_user = LoginForm()

    if form_login_user.validate_on_submit():
        email = form_login_user.email.data
        password = form_login_user.password.data

        find_email = db.session.execute(db.select(User).filter_by(email=email)).first()


        if not find_email:
            flash("That email does not exist. Please try again")
            return redirect(url_for('login'))
        elif not check_password_hash(find_email[0].password, password):
            flash("Email or password incorrect, please try again")
            return(redirect(url_for('login')))
        else:
            login_user(find_email[0])
            return redirect(url_for('home'))



    return render_template("login.html", form=form_login_user, logged_in = current_user.is_authenticated)






@app.route("/register", methods=['GET', 'POST'])
def register():
    form_new_user = RegisterForm()
    
    if form_new_user.validate_on_submit():
        email = form_new_user.email.data
        name = form_new_user.name.data
        password = form_new_user.password.data

        #### check if the email already exist on DB
        email_check = db.session.execute(db.select(User).filter_by(email=email)).first()

        if email_check == None:
            #### change to hash password for safety
            hash_and_salted_password = generate_password_hash(
                password,
                method='pbkdf2:sha256',
                salt_length=16
            )

            new_user = User(
                name = name,
                email = email,
                password = hash_and_salted_password
            )

            ### try to save into DB

            try:
                db.session.add(new_user)
                db.session.commit()

                #### log the user
                login_user(new_user)


            except Exception as e:
                print(e)
            

            return redirect(url_for('home'))
        

        else:    
            flash("You've already signed up with that email, log in instead")
            return redirect(url_for('login'))


    return render_template("register.html", form = form_new_user, logged_in = current_user.is_authenticated)






@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/new_product", methods = ['GET', 'POST'])
def new_product():
    # print("HOME Print ", current_user.is_authenticated)
    new_product = NewProduct()

    if new_product.validate_on_submit():
        
        name = new_product.name.data
        description = new_product.description.data
        price = new_product.price.data
        photo = new_product.photo.data

        new_product_db = Products(
            name = name,
            description = description,
            price = price,
            photo = photo
        )

        try:
            db.session.add(new_product_db)
            db.session.commit()

        except Exception as e:
            print(e)
        
        return redirect(url_for('home'))
  

    return render_template("new_product.html", form = new_product, logged_in = current_user.is_authenticated)
    # return render_template("index.html")







@app.route("/add", methods=['POST'])
def add():
    
    if request.method == 'POST':

        # print("ADD CART")
        # print(request.form['quantity'])
        # print(request.form['product_id'])

        try:
            quantity = int(request.form['quantity'])
            prod_id = request.form['product_id']

        except Exception as e:
            flash("Wrong Qty, please try again to update the cart")
            return redirect(url_for('home'))

        ### check DB with the Product ID

        product_added = db.session.execute(db.select(Products).filter_by(id=prod_id)).scalars().first()
        

        itemArray = { 
            str(product_added.id) : 
            {
                'name' : product_added.name, 
                'id' : product_added.id, 
                'quantity' : quantity, 
                'price' : product_added.price, 
                'image' : product_added.photo, 
                'total_price': quantity * product_added.price}
            }

        all_total_price = 0
        all_total_quantity = 0

        
        session.modified = True

        if 'cart_item' in session:

        
            found = False
            temp_id = 0
            for key, value in session['cart_item'].items(): 
 
                if value['id'] == product_added.id:
                    found = True    
                    temp_id = value['id']

            if found:

                new_quantity = int(session['cart_item'][str(temp_id)]['quantity']) + int(quantity)
                new_item_array =  { 
                        str(product_added.id) : 
                        {
                            'name' : product_added.name, 
                            'id' : product_added.id, 
                            'quantity' : new_quantity, 
                            'price' : product_added.price, 
                            'image' : product_added.photo, 
                            'total_price': new_quantity * product_added.price}
                        }
                
                session['cart_item'].update(new_item_array)


            else:
                session['cart_item'].update(itemArray)
                
                
            all_total_quantity = session['all_total_quantity'] + quantity
            all_total_price = session['all_total_price'] + (quantity * product_added.price)


        else:
            session['cart_item'] = itemArray
            all_total_quantity = all_total_quantity + quantity
            all_total_price = all_total_price + (quantity * product_added.price)

        session['all_total_quantity'] = all_total_quantity
        session['all_total_price'] = all_total_price
                  

    return redirect(url_for('home'))
    



    
@app.route("/cart", methods=['GET','POST'])
def shopping_cart():    
    
    return render_template("cart.html", logged_in = current_user.is_authenticated)





@app.route('/empty')
def empty_cart():
	try:
		session.clear()
		return redirect(url_for('home'))
	except Exception as e:
		print(e)






@app.route('/delete/<string:code>')
def delete(code):
    
    try:


        session['all_total_quantity'] = session['all_total_quantity'] - session['cart_item'][str(code)]['quantity']
        session['all_total_price'] = session['all_total_price'] - (session['cart_item'][str(code)]['quantity'] * session['cart_item'][str(code)]['price'] )

        (session['cart_item'].pop(str(code)))
        

        if session['all_total_quantity'] == 0 or session['all_total_price'] == 0:
            session.clear()

        return redirect(url_for('shopping_cart'))
    
        
    

    except Exception as e:
        print(e)
        flash("Something went wrong, try again")
        return redirect(url_for('shopping_cart'))



	# try:
	# 	all_total_price = 0
	# 	all_total_quantity = 0
	# 	session.modified = True
		
	# 	for item in session['cart_item'].items():
	# 		if item[0] == code:				
	# 			session['cart_item'].pop(item[0], None)
	# 			if 'cart_item' in session:
	# 				for key, value in session['cart_item'].items():
	# 					individual_quantity = int(session['cart_item'][key]['quantity'])
	# 					individual_price = float(session['cart_item'][key]['total_price'])
	# 					all_total_quantity = all_total_quantity + individual_quantity
	# 					all_total_price = all_total_price + individual_price
	# 			break
		
	# 	if all_total_quantity == 0:
	# 		session.clear()
	# 	else:
	# 		session['all_total_quantity'] = all_total_quantity
	# 		session['all_total_price'] = all_total_price
		
	# 	return redirect(url_for('cart'))
	# except Exception as e:
	# 	print(e)


        
        



@app.route("/", methods=['GET', 'POST'])
def home():
    # print("HOME Print ", current_user.is_authenticated)

    if request.method == 'POST':
        pass

    products_show = db.session.execute(db.select(Products)).scalars().all()
    

    return render_template("index.html", logged_in = current_user.is_authenticated, products=products_show)
    # return render_template("index.html")



# def array_merge( first_array , second_array ):
# 	if isinstance( first_array , list ) and isinstance( second_array , list ):
# 		return first_array + second_array
# 	elif isinstance( first_array , dict ) and isinstance( second_array , dict ):
# 		return dict( list( first_array.items() ) + list( second_array.items() ) )
# 	elif isinstance( first_array , set ) and isinstance( second_array , set ):
# 		return first_array.union( second_array )
# 	return False



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

