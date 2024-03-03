from flask import Flask, render_template, request, redirect, url_for, session
import pymongo
import os
import bcrypt
from dotenv import load_dotenv
import datetime
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename

load_dotenv()

UPLOAD_FOLDER = 'static/image'



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# mongoDB connection
client = pymongo.MongoClient(os.getenv('mongodb+srv://se_team8:GUwSJle33mNZ2yzW@team8.ze5o0ww.mongodb.net/'))
db = client[os.getenv('seven')]
users = db["users"]
posts = db["posts"]

# ---------------------------- user authenticatoin & account management --------------------------- #
# user register
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = db.users
        existing_user = users.find_one({'username': request.form['username']})
        
        if existing_user is None:
            name = request.form['name']
            hashpass = bcrypt.hashpw(request.form['password'], bcrypt.gensalt())
            users.insert_one({'username': request.form['username'], 'password': hashpass, 'name': name})
            session['username'] = request.form['username'] #should session be username or name?
            return redirect(url_for('home'))
        
        return 'That username already exists!'
    
    return render_template('register.html')



# user login check
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        users = db.users
        login_user = users.find_one({'username': request.form['username']})
        
        if login_user:
            #if check_password_hash(login_user['password'], request.form['password']):
            if bcrypt.checkpw(request.form['password'], login_user['password']):
                session['username'] = request.form['username']
                return redirect(url_for('home'))
        else: 
            return 'User not found! Please register first.'
            
        return 'Wrong username or password > :('
    
    return redirect(url_for('home'))


# user logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))



# profile page edits: user can change their username/email and password
# change username
@app.route('/profile_update', methods=['POST'])
def change_info():
    update_fields = {}
    
    new_name = request.form.get('name')
    new_username = request.form.get('email')
    new_password = request.form.get('password')
    
    if new_name:
        update_fields['name'] = new_name
    
    if new_username:
        # check if the username is already taken
        if users.find_one({'username': new_username}):
            return 'Username already taken!'
        update_fields['username'] = new_username
    
    if new_password:
        # hash new password
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        update_fields['password'] = hashed_new_password
    
    if not update_fields:
        return 'No changes made!'
    
    result = users.update_one({'username': session['username']}, {'$set': update_fields})
    
    # update username in seesion if updated successfully
    if 'username' in update_fields and result.modified_count == 1:        # == 1 or > 0?
        session['username'] = new_username
    
    
    if result.modified_count == 1:
        return redirect(url_for('individual-profile.html'))
        #return 'Profile updated successfully!'
    
    # if the update failed
    return redirect(url_for('individual-profile.html'))


# ----------------------------- entry management ----------------------------- #

# show posts by week
@app.route('/allposts', methods=['GET'])
def all_posts():
    if 'username' not in session: # if user is not logged in
        return redirect(url_for('login'))
    
    username = session['username']
    all_posts = posts.find({'username': username})
    posts_list = list(all_posts)
    
    return render_template('home.html', posts=posts_list)



# show home page where it has weekly feed
# is home page the same as all_posts?
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'username' not in session: # if user is not logged in
        return redirect(url_for('login'))
    
    search_query = None
    
    user = users.find_one({'username': session['username']})
    displayed_posts = posts.find({'username': session['username']}).sort('time_created', -1)
    
    if request.method == 'POST' and 'date' in request.form:
        date_str = request.form['date']
        if date_str:
            try:
                displayed_posts = posts.find({'username': session['username'], 'date': date_str}).sort('time_created', -1)
                
                # keep the search query to display on the page
                search_query = date_str
                
            except ValueError:
                return 'Invalid date format! Please use mm-dd-yyyy.'
    
    return render_template('home_page.html', user=user, posts=displayed_posts, search_query=search_query)



# display user info/profile
@app.route('/profile', method=['GET'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = users.find_one({'username': session['username']})
    
    return render_template('individual-profile.html', user=user)

    


# show a specific post when it is clicked on the home page
@app.route('/post/<post_id>')
def show_post(post_id):
    post = posts.find_one({'_id': ObjectId(post_id)})
    
    return render_template('post.html', post=post)


# upload post
@app.route('/upload', methods=['POST'])
def upload_post():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    text = request.form['text'] #text from the form in html 
    image = request.files.get('image') # image from the form in html
    
    image_path = None # if there is no image uploaded
    if image:
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        image_path = os.path.join('/static/image', filename)
        
    
    post = {
        'username': session['username'],
        'name': session['name'],
        'text': text,
        'image_path': image_path,
        'time_created': datetime.datetime.utcnow(),
        'date': datetime.date.today().strftime("%m-%d-%Y") # date is stored as a string in mm-dd-yyyy
    }

    # insert post
    posts.insert_one(post)
    
    return redirect(url_for('home'))


    

# delete a post
@app.route('/delete/<post_id>')
def delete_post(post_id):
    posts.delete_one({'_id': ObjectId(post_id)})
    return redirect(url_for('home'))


# edit an exsiting post
@app.route('/edit/<post_id>', methods=['POST'])
def edit_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    new_text = request.form['post-text'] #check with html form name
    
    # update the post with the new text
    posts.update_one({'_id': ObjectId(post_id)}, {'$set': {'text': new_text}})
    
    return redirect(url_for('home'))





# ---------------------------------------------------------------------------- #
#                                     main                                     #
# ---------------------------------------------------------------------------- #

if __name__ == '__main__':
    FLASK_PORT = os.getenv('FLASK_PORT', '5000')
    app.run(port=FLASK_PORT)