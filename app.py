from flask import Flask, render_template, request, redirect, url_for, session
import pymongo
import os
import bcrypt
from dotenv import load_dotenv
import datetime
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from io import BytesIO
#from bson.binary import Binary
#from PIL import Image
#import base64

load_dotenv()

UPLOAD_FOLDER = '/images'



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "323qssssa"



DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("MONGODB_PW")
DB_HOST = os.getenv("DB_HOST")
uri = f"mongodb+srv://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/?retryWrites=true&w=majority&appName=Cluster0&tlsAllowInvalidCertificates=true"
client = pymongo.MongoClient(uri)
db = client.get_database("seven")
user_collection = db.get_collection("users")
post_collection = db.get_collection("posts")

# the following try/except block is a way to verify that the database connection is alive (or not)
try:
    # verify the connection works by pinging the database
    client.admin.command("ping")  # The ping command is cheap and does not require auth.
    print(" *", "Connected to MongoDB!")  # if we get here, the connection worked!
except Exception as e:
    # the ping command failed, so the connection is not available.
    print(" * MongoDB connection error:", e)  # debug

# ---------------------------- user authenticatoin & account management --------------------------- #
# user register
""" @app.route('/register', methods=['POST', 'GET'])
def register():
    message = None
    if request.method == 'POST':
        new_name = request.form['name']
        new_username = request.form['username']
        new_password = request.form['password']

        existing_user = users.find_one({'username': new_username})
        #existing_user = users.find({})
        
        if existing_user is None:
            hashpass = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'username': new_username, 'password': hashpass, 'name': new_name})
            session['username'] = new_username
            return redirect(url_for('home'))
        
        message = 'That username already exists!'
        return render_template('sign-up.html', message=message)
    
    return render_template('sign-up.html', message=message)  """

@app.route('/register', methods=['POST', 'GET'])
def register():
    message = None
    if request.method == 'POST':
        new_name = request.form['name']
        new_username = request.form['username']
        new_password = request.form['password']

        existing_user = user_collection.find_one({'username': new_username})
        #existing_user = user_collection.find({})
        #print(existing_user)
        
        if existing_user is None:
            #hashpass = bcrypt.hashpw(new_password, bcrypt.gensalt())
            hashpass = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user_collection.insert_one({'username': new_username, 'password': hashpass, 'name': new_name})
            session['username'] = new_username
            return redirect(url_for('home'))

        
        message = 'That username already exists!'
        return render_template('sign-up.html', message=message)
    
    return render_template('sign-up.html', message=message) 
   


""" @app.route('/register', methods=['POST'])
def register():
    message = None

    new_name = request.form['name']
    new_username = request.form['username']
    new_password = request.form['password']

    existing_user = users.find_one({'username': new_username})
    
    if existing_user is None:
        hashpass = bcrypt.hashpw(new_password, bcrypt.gensalt())
        users.insert_one({'username': new_username, 'password': hashpass, 'name': new_name})
        session['username'] = new_username
        return redirect(url_for('home'))
    
    message = 'That username already exists!'
    return render_template('sign-up.html', message=message) 
    
    # return render_template('sign-up.html', message=message) """


# user login check
@app.route('/', methods=['POST', 'GET'])
def login():
    message = None
    if request.method == 'POST':
        login_user = user_collection.find_one({'username': request.form['username']})
        
        if login_user:
            if bcrypt.checkpw(request.form['password'].encode('utf-8'), login_user['password']):
                session['username'] = request.form['username']
                return redirect(url_for('home'))
        else: 
            message = 'User not found! Please register first.'
            # return redirect(url_for('log-in'))
            return render_template('log-in.html', message=message)
        
        message = 'Wrong username or password. Please try again.'    
        return render_template('log-in.html', message=message)
        # return redirect(url_for('login')) 
    
   #  return redirect(url_for('home'))
    return render_template('log-in.html', message=message) 

""" @app.route('/', methods=['POST', 'GET'])
def login():
    message = None
    if request.method == 'POST':
        login_user = user_collection.find_one({'username': request.form['username']})
        
        if login_user:
            if request.form['password'] == login_user['password']:
                session['username'] = request.form['username']
                return redirect(url_for('home'))
        else: 
            message = 'User not found! Please register first.'
            # return redirect(url_for('log-in'))
            return render_template('log-in.html', message=message)
        
        message = 'Wrong username or password. Please try again.'    
        return render_template('log-in.html', message=message)
        # return redirect(url_for('login')) 
    
   #  return redirect(url_for('home'))
    return render_template('log-in.html', message=message) """


# user logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/edit_prof')
def show_edit_prof_form():
    return render_template('edit-profile.html')



# profile page edits: user can change their username/email and password
# change username
@app.route('/profile_update', methods=['POST'])
def change_info():
    message = None
    update_fields = {}
    
    new_name = request.form.get('name')
    new_username = request.form.get('username')
    new_password = request.form.get('password')
    image = request.files.get('profile_pic') # image from the form in html
    
    image_path = None # if there is no image uploaded
    
    if image:
        #image_data = image.read()
        #binary_data = Binary(image_data)

        
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        image_path = filepath
        
        update_fields['pfp_file_path'] = binary_data

    if new_name:
        update_fields['name'] = new_name
    
    if new_username:
        # check if the username is already taken
        if user_collection.find_one({'username': new_username}):
            message = 'Username already taken!'
            return render_template('edit-profile.html', message=message)
        
        update_fields['username'] = new_username
    
    if new_password:
        # hash new password
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        update_fields['password'] = hashed_new_password
    
    if not update_fields:
        message = 'No changes made!'
        return render_template('edit-profile.html', message=message)
    
    result = user_collection.update_one({'username': session['username']}, {'$set': update_fields})
    
    # update username in seesion if updated successfully
    if 'username' in update_fields and result.modified_count == 1:        # == 1 or > 0?
        session['username'] = new_username
    
    
    if result.modified_count == 1:
        return redirect(url_for('profile'))
        #return 'Profile updated successfully!'
    
    # if the update failed
    return redirect(url_for('profile'))


# ----------------------------- entry management ----------------------------- #

# show posts by week
""" @app.route('/allposts', methods=['GET'])
def all_posts():
    if 'username' not in session: # if user is not logged in
        return redirect(url_for('login'))
    
    username = session['username']
    all_posts = posts.find({'username': username})
    posts_list = list(all_posts)
    
    return render_template('home.html', posts=posts_list) """



# show home page where it has weekly feed
# is home page the same as all_posts?
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'username' not in session: # if user is not logged in
        return redirect(url_for('login'))
    
    search_query = None
    
    user = user_collection.find_one({'username': session['username']})
    displayed_posts = post_collection.find({'username': session['username']}).sort('time_created', -1)
    
    if request.method == 'POST' and 'date' in request.form:
        date_str = request.form['date']
        if date_str:
            try:
                displayed_posts = post_collection.find({'username': session['username'], 'date': date_str}).sort('time_created', -1)
                
                # keep the search query to display on the page
                search_query = date_str
                
            except ValueError:
                search_query = 'Invalid date format! Please use mm-dd-yyyy.'
                return render_template('home_page.html', user=user, posts=displayed_posts, search_query=search_query)
    
    return render_template('home_page.html', user=user, posts=displayed_posts, search_query=search_query)



# display user info/profile
@app.route('/profile', methods=['GET'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = user_collection.find_one({'username': session['username']})
    """
    if user['pfp_file_path'] != None:
        image_binary = user['pfp_file_path']
        image_stream = BytesIO(image_binary)
    """
    return render_template('individual-profile.html', user=user)

    


# show a specific post when it is clicked on the home page
@app.route('/post/<post_id>')
def show_post(post_id):
    post = post_collection.find_one({'_id': ObjectId(post_id)})
    #image_path=post['image_path']
    #encoded_image = base64.b64encode(image_path).decode('utf-8')
    
    return render_template('post.html', post=post)


@app.route('/show_post_form')
def show_post_form():
    return render_template('upload_post.html')



# upload post
@app.route('/upload', methods=['POST'])
def upload_post():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    text = request.form['text'] #text from the form in html 
    image = request.files.get('image') # image from the form in html
    
    
    image_path = None # if there is no image uploaded
    if image:
        """
        out = BytesIO()
        with Image.open(image) as img:
            img.save(out, format='png')
        image_path = out.getvalue()
 
        """
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        image_path = filepath
    
    username = session.get('username')
    name = session.get('name')
    
    post = {
        'username': username,
        'name': name,
        'text': text,
        'image_path': image_path,
        'time_created': datetime.datetime.utcnow(),
        'date': datetime.date.today().strftime("%Y-%m-%d") # date is stored as a string in mm-dd-yyyy
    }

    # insert post
    post_collection.insert_one(post)
    
    return redirect(url_for('home'))


    

# delete a post
@app.route('/delete/<post_id>')
def delete_post(post_id):
    post_collection.delete_one({'_id': ObjectId(post_id)})
    return redirect(url_for('home'))



@app.route('/edit-post/<post_id>')
def show_edit_form(post_id):
    post = post_collection.find_one({"_id": ObjectId(post_id)})
    return render_template('edit-post.html', post=post)


# edit an exsiting post
@app.route('/edit/<post_id>', methods=['POST'])
def edit_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    new_text = request.form['post-text'] #check with html form name
    
    # update the post with the new text
    post_collection.update_one({'_id': ObjectId(post_id)}, {'$set': {'text': new_text}})
    
    return redirect(url_for('home'))





# ---------------------------------------------------------------------------- #
#                                     main                                     #
# ---------------------------------------------------------------------------- #

if __name__ == '__main__':
    FLASK_PORT = os.getenv('FLASK_PORT', '8080')
    app.run(port=FLASK_PORT)
