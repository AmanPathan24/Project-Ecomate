from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv
import csv
import os

load_dotenv()               #Used to load environment variables from a .env file (for security)

app = Flask(__name__)         #Used to create a Flask Application Instance
app.secret_key = "your_secret_key"        #Required to store the session across different pages

# Flask-Mail configuration (SMTP - Simple Mail Transfer Protocol)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'             #Using Gmail's SMTP Server 
app.config['MAIL_PORT'] = 587                           #General address for sending email securely over TLS
app.config['MAIL_USE_TLS'] = True                       #TLS(Transport Layer Security)
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')   # Gmail address taken from .env file
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')   # App Password taked from .env file
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USER') 

mail = Mail(app)                        #Creates a flask mail instance

def email_exists(email):                       # Function to check if email exists in the CSV file
    try:
        with open('users.csv', mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[1] == email:  # Check email
                    return row  # Return the row if email exists
    except FileNotFoundError:
        return None
    return None

def username_exists(username):             # Function to check if username exists in the CSV file
    try:
        with open('users.csv', mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == username:  # Check username
                    return True  # Return True if username exists
    except FileNotFoundError:
        return False
    return False

def send_promotional_email(email, subject, body):       # Function to send emails
    try:
        msg = Message(subject, recipients=[email])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/')                          #Redirects to the main url(5000 port)
def index():
    if 'user' in session:
        return redirect(url_for('home'))        #Redirects to the homepage if user is logged in
    return redirect(url_for('getstarted'))      #Redirects to the getstarted page if not logged in

@app.route('/home')
def home():                             #Renders the index.html template for the homepage
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():                       #Function to check user credentials on the signup page
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if email_exists(email):
            error_message = "Account already exists with this email. Please log in."       #User mail checking
            return render_template('signup.html', error=error_message)
        
        if username_exists(username):
            error_message = "Username already exists. Please choose another one."           #Username checking 
            return render_template('signup.html', error=error_message)

        location = "Pune"                # Default location
        waste_contribution = 0               # Default waste contribution

        # Save new user data to CSV file
        try:
            with open('users.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                # Saving username, email, password, location, and waste_contribution in separate columns (each entry should be a new row)
                writer.writerow([username, email, password, location, waste_contribution])
        except Exception as e:
            print(f"Error saving user data: {e}")
            error_message = "There was an error saving your account. Please try again."
            return render_template('signup.html', error=error_message)

        # Sending personalised Welcome email to user
        subject = "Welcome to EcoMate!"         #Mail main body and content
        body = f'''
Welcome to EcoMate, {username}! 🌱  

Hi {username},  

We’re so excited to welcome you to the EcoMate community – where smart waste management meets sustainability. Thank you for joining us on this journey to make a positive impact on the planet. Together, we can create a cleaner, greener future!  

What You Can Do on EcoMate: 
🌍 Locate Smart Dustbins Near You: 
Use our platform to find nearby dustbins for proper waste disposal and recycling.  

🥁 Get Personalized Recycling Tips:
Learn how to segregate waste, reduce single-use plastics, and adopt eco-friendly habits.  

🛢️ Track Your Contributions:  
Monitor your progress and see how your actions contribute to a cleaner environment.  

Get Started:  
1. Log in to your account  
2. Set up your profile to unlock personalized features.  
3. Explore our resources and start making a difference today!  

Thank you for being part of our mission!  

Warm regards,  
The EcoMate Team  
        '''
        send_promotional_email(email, subject, body)            #Using the function defined above

        session['user'] = username
        return redirect(url_for('home'))
    return render_template('signup.html', error=None)

@app.route('/Feedback')
def feedback():             #Function to render Feedback.html template for Feedback page
    return render_template('Feedback.html')


# Ensure the feedback.csv file exists
if not os.path.exists("Feedback.csv"):          #Creating feedback csv file if it does not exists
    with open("Feedback.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Email", "Feedback"])


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():                  #Function to get and store the feedback from user to feedback.csv file
    try:
        # Get feedback data from request
        feedback_data = request.get_json()
        name = feedback_data.get("name")
        email = feedback_data.get("email")
        feedback = feedback_data.get("feedback")

        # Append the feedback to feedback.csv
        with open("Feedback.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([name, email, feedback])

        # Redirect to /home with a success message
        return jsonify({"message": "Feedback sent"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "An error occurred while processing your feedback."}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():                #Function to check and login pre-existing user
    if request.method == 'POST':
        email = request.form['user_email']
        password = request.form['password']

        user = email_exists(email)
        if not user:                #Checking if user has an account or not
            error_message = "User does not exist. Please create an account."
            return render_template('login.html', error=error_message)

        if user[2] != password:
            error_message = "Invalid password. Please try again."
            return render_template('login.html', error=error_message)

        # Successful login
        session['user'] = user[0]

        subject = "Login Alert - EcoMate"
        body = f"Hello {user[0]},\n\nYou just logged into EcoMate. If this wasn't you, please contact support."
        send_promotional_email(email, subject, body)

        return redirect(url_for('home'))

    return render_template('login.html', error=None)

@app.route('/logout')
def logout():           #Function to redirect user to signup page after clicking logout
    session.pop('user', None)
    return redirect(url_for('signup'))

@app.route('/recycling')
def recycling_options():            #Function to render recycling.html template for recylcing page
    return render_template('recycling.html')

@app.route('/settings')
def settings():                 #Function to render settings.html template for settings page
    return render_template('settings.html')

@app.route('/community')
def community():                #Function to render community.html template for Community page
    return render_template('community.html')

@app.route('/profile')              # Route to display user profile
def profile():              #Function to redirect user to login page if not logged in
    if 'user' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    # Fetch user profile from the CSV file
    user_data = get_user_data(session['user'])
    if not user_data:
        return "User not found", 404
    
    return render_template('profile.html', user=user_data)

@app.route('/update_profile_page', methods=['GET'])         # Route to display update profile page
def update_profile_page():          #Function to redirect user to login page if not logged in
    if 'user' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    # Fetch user profile from the CSV file
    user_data = get_user_data(session['user'])
    if not user_data:
        return "User not found", 404
    
    return render_template('update_profile.html', user=user_data)

@app.route('/update_profile', methods=['POST'])     # Route to handle updating the profile
def update_profile():            #Function to update profile of user in csv file and webpage
    if 'user' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    # Get updated profile data from the form
    updated_data = {
        'username': request.form['username'],
        'email': request.form['email'],
        'location': request.form['location'],
        'waste_contribution': request.form['waste_contribution'],
    }

    # Update user data in CSV
    update_user_data(session['user'], updated_data)

    # Redirect back to the profile page
    return redirect(url_for('profile'))

def get_user_data(username):            #Function to get user data from the CSV file
    try:
        with open('users.csv', mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == username:  # Check username stored in the 1st column
                    return {
                        'username': row[0],
                        'email': row[1],
                        'location': row[3],  #We have location in the 4th column
                        'waste_contribution': row[4]  #We have waste contribution stored in 5th column
                    }
    except FileNotFoundError:
        return None
    return None

def update_user_data(username, updated_data):       #Function to update user data in the CSV file
    try:
        rows = []
        with open('users.csv', mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Find and update the user's row
        for row in rows:
            if row[0] == username:
                row[1] = updated_data['email']
                row[3] = updated_data['location']
                row[4] = updated_data['waste_contribution']
                break

        # Write the updated data back to the CSV
        with open('users.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    except Exception as e:
        print(f"Error updating user data: {e}")

@app.route('/getstarted')
def getstarted():           #Function to render getstarted.html template for Pre-Login page     
    return render_template('getstarted.html')

@app.route('/dustbins')
def get_dustbins():          #Function to open the dustbin api
    dustbins = load_dustbins()
    return jsonify(dustbins)

@app.route('/binsnearme')
def bins_near_me():          #Function to render binsnearme.html template for Bins Near Me page  
    return render_template('binsnearme.html')

def load_dustbins():            #Function to load the dustbin api and read coordinates from the dustbin.csv file
    dustbins = []
    try:
        with open('dustbins.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                dustbins.append({
                    'name': row['name'],
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude'])
                })
    except FileNotFoundError:
        print("dustbins.csv file not found.")
    return dustbins

@app.route('/knowyourwaste')
def knowyourwaste():        #Function to render knowyourwaste.html template for Know Your Waste page
    return render_template('knowyourwaste.html')

@app.route('/biodegradable')
def biodegradable():        #Function to render biodegradable.html template for Biodegradable page
    return render_template('biodegradable.html')

@app.route('/Agriculture')
def Agriculture():             #Function to render Agriculture.html template for Agriculture page
    return render_template('Agriculture.html')


@app.route('/chemical')
def chemical():             #Function to render chemical.html template for Chemical page
    return render_template('chemical.html')

@app.route('/biomedical')
def biomedical():           #Function to render biomedical.html template for Biomedical page
    return render_template('biomedical.html')

@app.route('/electronicwaste')
def electronicwaste():          #Function to render electronicwaste.html template for Electronic Waste page
    return render_template('electronicwaste.html')

@app.route('/industrialwaste')
def industrialwaste():            #Function to render industrial.html template for Industrial page
    return render_template('industrialwaste.html')

@app.route('/foodwaste')
def foodwaste():                #Function to render foodwaste.html template for Food Waste page
    return render_template('foodwaste.html')

@app.route('/recycle_metal')
def recycle_metal():            #Function to render metal_recycle.html template for Metal Recyle page
    return render_template('recycle_techniques_metal.html')

@app.route('/recycle_glass')
def recycle_glass():             #Function to render glass_recycle.html template for Glass Recyle page
    return render_template('recycle_techniques_glass.html')

@app.route('/recycle_electronics')
def recycle_electronics():           #Function to render electronics_recycle.html template for Electronics Recyle page
    return render_template('recycle_techniques_electronics.html')

@app.route('/recycle_plastic')
def recycle_plastic():               #Function to render plastic_recycle.html template for Plastic Recyle page
    return render_template('recycle_techniques_plastic.html')

@app.route('/5tips')
def fivetips():              #Function to render 5tips.html template for 5 Tips page
    return render_template('5tips.html')

@app.route('/diy')
def diy():               #Function to render diy.html template for DIY page
    return render_template('diy.html')

@app.route('/commu3')
def commu3():               #Function to render commu3.html template for Community page
    return render_template('commu3.html')

@app.route('/commu4')
def commu4():               #Function to render commu4.html template for Community page
    return render_template('commu4.html')

@app.route('/create_community')
def create_community():         #Function to render create_commiunity.html template for Creating Community page
    return render_template('create_community.html')

@app.route('/join_community')
def join_community():           #Function to render join_community.html template for Join Community page
    return render_template('join_community.html')

suggestions = [                           #Search bar contents in the drop down list and their url to route
    { "text": "Biodegradable Waste", "url": "/biodegradable" },
    { "text": "Biomedical Waste", "url": "/biomedical" },
    { "text": "Chemical Waste", "url": "/chemical" },
    { "text": "Electronic Waste", "url": "/electronicwaste" },
    { "text": "Industrial Waste", "url": "/industrialwaste" },
    { "text": "Agriculture Waste", "url": "/agriculture" },
    { "text": "Settings", "url": "/settings" },
    { "text": "Profile", "url": "/profile" },
    { "text": "Tips", "url": "/5tips" },
    { "text": "Community", "url": "/community" },
    { "text": "Recycling", "url": "/recycling" },
    { "text": "Food Waste", "url": "/foodwaste" }
]

@app.route('/search', methods=['GET'])
def search():                                 #Function for the search bar
    query = request.args.get('query', '').lower()
    filtered_suggestions = [s for s in suggestions if query in s['text'].lower()]
    
    # Optionally, handle search results dynamically
    if filtered_suggestions:
        return f"<h1>Search Results for '{query}'</h1>" + "".join(
            f"<p><a href='{s['url']}'>{s['text']}</a></p>" for s in filtered_suggestions
        )
    else:
        return f"<h1>No results found for '{query}'</h1><p>Try a different search query.</p>"


if __name__ == '__main__':          #Used to run the Flass app
    app.run(debug=True)
