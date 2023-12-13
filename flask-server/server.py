from flask import Flask, jsonify, request,make_response
from flask_mysqldb import MySQL
from datetime import timedelta,timezone,datetime
import string,secrets,requests
import jwt
from jwt.exceptions import ExpiredSignatureError
import hashlib
import yaml,json,os
from passlib.hash import sha256_crypt
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity,unset_jwt_cookies, jwt_required, JWTManager
from flask_cors import CORS, cross_origin
import base64,openai
import pickle
import tensorflow as tf
from tensorflow import keras
from keras.layers import Dense
from keras.models import Sequential, load_model
import numpy as np
import base64,io,cv2
from PIL import Image
openai.api_key = os.getenv("API_KEY")
app = Flask(__name__)
CORS(app,supports_credentials=True)
app.config["JWT_SECRET_KEY"] = "ooh_so_secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_HTTPONLY'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'Strict'
jwt = JWTManager(app)
db = yaml.full_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
# app.config['PORT'] = 33060
mysql = MySQL(app)
import models

def verify_jwt_token():
    jwt_token = request.cookies.get("access_token")  # Retrieve the JWT token from the httpOnly cookie
    print(jwt_token)
    if not jwt_token:
        print("token not found")
        return False
    
    try:
        return True
    except ExpiredSignatureError:
        return False


@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(hours=1))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token 
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response

@app.route('/emotion',methods=['POST'])
@cross_origin(supports_credentials=True)
def getEmotion():
    model = load_model('./models/emotion_model.h5')
    image = request.json['image']
    image = Image.open(io.BytesIO(base64.decodebytes(bytes(image,"utf-8"))))
    image.save('tmp.png')
    image = cv2.imread('tmp.png')
    image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    image = cv2.resize(image,(48,48))
    image = np.array(image)
    image = np.expand_dims(image,axis=0)
    image = image/255
    resp = model.predict(image)
    print(resp)
    predicted_class = np.argmax(resp)
    class_names = ['positive','negative','neutral']
    return jsonify({'prediction':class_names[predicted_class]})

@app.route('/likes',methods=['POST'])
@cross_origin(supports_credentials=True)
def likes():
    like = request.get_json()
    like = [like]
    print(like)
    svm = pickle.load(open('./models/likes/svm.txt','rb'))
    dt = pickle.load(open('./models/likes/dt.txt','rb'))
    gb = pickle.load(open('./models/likes/gb.txt','rb'))
    knn = pickle.load(open('./models/likes/knn.txt','rb'))
    lr = pickle.load(open('./models/likes/lr.txt','rb'))
    nb = pickle.load(open('./models/likes/nb.txt','rb'))
    rand = pickle.load(open('./models/likes/rand.txt','rb'))
    career = set()
    career.add(svm.predict(like)[0])
    career.add(dt.predict(like)[0])
    career.add(gb.predict(like)[0])
    career.add(knn.predict(like)[0])
    career.add(lr.predict(like)[0])
    career.add(nb.predict(like)[0])
    career.add(rand.predict(like)[0])
    career = list(career)
    print(career)
    return jsonify(career)

@app.route('/career',methods=['POST'])
@cross_origin(supports_credentials=True)
def career():
    LR_score = int(request.json['LR_Score'])
    VA_score = int(request.json['VA_Score'])
    AR_Score = int(request.json['AR_Score'])
    Memory = int(request.json['mem'])
    # rand = pickle.load('./models/rand.txt')
    #report = [[75,50,10,10]]
    report = [[LR_score,VA_score,AR_Score,Memory]]
    svm = pickle.load(open('./models/svm.txt','rb'))
    dt = pickle.load(open('./models/dt.txt','rb'))
    nb = pickle.load(open('./models/nb.txt','rb'))
    career = set()
    print(svm.predict(report))
    print(dt.predict(report))
    print(nb.predict(report))
    career.add(svm.predict(report)[0])
    career.add(dt.predict(report)[0])
    career.add(nb.predict(report)[0])
    career = list(career)
    print(career)
    return jsonify(career)


@app.route('/login',methods=['POST'])
@cross_origin(supports_credentials=True)
def login():
    users = models.Table("users","Email_ID","Password")
    email = request.json['Email_ID']
    password = request.json['Password']
    hashed_password = sha256_crypt.hash(password)
    print(hashed_password)
    user = users.getone("Email_ID",email)
    if user is None:
        print("Outer if reached")
        return jsonify(status="User Not Found")
    else:
        og_pass = user[1]
        if not sha256_crypt.verify(password,og_pass):
            return jsonify(status="Invalid Password")
        else:
            access_token = create_access_token(identity=email)
            ut=user[2]
            response=make_response(jsonify(status="Auth Success!",atk=access_token,user_type=ut))
            response.set_cookie('access_token',access_token)
            return response

@app.route('/deleteUser',methods=['POST'])
@cross_origin(supports_credentials=True)
def deleteUser():
    users=models.Table("users","Email_Id")
    email=request.json["Email_Id"]
    result=users.deleteOne("Email_Id",email)
    print(result)
    if result==True:
        return jsonify(status="success")
    else:
        return jsonify(status="failure")

@app.route('/deleteBlog',methods=['POST'])
@cross_origin(supports_credentials=True)
def deleteBlog():
    blogs=models.Table("blogs","Id")
    id=request.json["Id"]
    result=blogs.deleteOne("id",id)
    print(result)
    if result==True:
        return jsonify(status="success")
    else:
        return jsonify(status="failure")

@app.route('/deletePsy',methods=['POST'])
@cross_origin(supports_credentials=True)
def deletePsy():
    psy=models.Table("psy","Id")
    id=request.json["Id"]
    result=psy.deleteOne("id",id)
    print(result)
    if result==True:
        return jsonify(status="success")
    else:
        return jsonify(status="failure")


@app.route('/chatbot', methods=['POST'])
@cross_origin(supports_credentials=True)
def chatbot():
    message = request.get_json()["message"]
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": "You are gyanibot, a supportive companion for my mental health journey"},
            {"role": "user", "content": message},
    ],
    temperature=0,
)

    return jsonify(bot_response=response['choices'][0]['message']['content'])
    # return jsonify(bot_response="I have received your message. You are OP...Your are awesome!!")


@app.route('/getSentiment', methods=['POST'])
@cross_origin(supports_credentials=True)
def getSentiment():
    text=request.json['message']
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "user", "content": "Give Sentiment Analysis for the text you will be given in a length from one word minimum to 10 words maximum"},
            {"role": "user", "content": text},
    ],
    temperature=0,
)

    return jsonify(sentiment=response['choices'][0]['message']['content'])

@app.route('/checkMail', methods=['POST'])
@cross_origin(supports_credentials=True)
def check():
    email=request.get_json()
    users = models.Table("users","Email_ID")
    user=users.getone("Email_ID",email)
    genotp=''.join(secrets.choice(string.ascii_uppercase + string.digits)
                            for i in range(7))
    if user is None:
        return jsonify(status="User not Found")
    else:
        url = "https://email-authentication-system.p.rapidapi.com/"

        querystring = {"recipient":email,"app":"Login System"}

        headers = {
            "X-RapidAPI-Key": "9eabe601b6msh1ea06cb8d54a0d4p15c5ffjsn511bfb4c034f",
            "X-RapidAPI-Host": "email-authentication-system.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        response_json=response.json()
        print(response.status_code)
        if response.status_code==202 or response.status_code == 200:
            resp = make_response(jsonify(status="found"))
            # Set the cookie
            resp.set_cookie('hash',response_json['authenticationCode'] )
            return resp
        else:
            return jsonify(status="Not found")

@app.route('/getUsers',methods=['POST'])
@cross_origin(supports_credentials=True)
def getUsers():
    token = verify_jwt_token()
    if not token:
        return jsonify(message='Invalid or expired JWT token'), 401
    users=models.Table("users","Email_ID","FirstName","LastName","Institution","Class","Stream","Specialty","DOB","user_type")
    results=users.getall(1,1)
    if results is None:
        return jsonify([])
    return jsonify(results) 
   


@app.route('/getHash',methods=['POST'])
@cross_origin(supports_credentials=True)
def hashkaro():
    # Get the JSON data and encode it to bytes
    json_data = request.get_json()
    json_data_bytes = json_data.encode('utf-8')
    
    # Calculate the MD5 hash
    otp = hashlib.md5(json_data_bytes).hexdigest()
    
    cookiedata = request.cookies.get('hash')
    print(f"cookiedata",cookiedata)
    print("otp",otp)
    if cookiedata == otp:
        response = jsonify(status='ok')
        response.set_cookie('hash', max_age=0)
        return response
    else:
        response = jsonify(status='unauthorized')
        response.set_cookie('hash', max_age=0)
        return response
    
@app.route('/updatePassword',methods=['POST'])
@cross_origin(supports_credentials=True)
def updatePassword():
    email=request.json['email']
    newPassword=request.json['newPassword']
    users=models.Table("users","Email_ID","Password")
    hashed_password = sha256_crypt.hash(newPassword)
    user=users.updateOne(hashed_password,"Password",email)
    if user is None:
        return jsonify(status="fail")
    else:
        return jsonify(status="success")

@app.route('/updateUserDetails',methods=['POST'])
@cross_origin(supports_credentials=True)
def updateUserProfile():
    try:
        data = request.get_json()
        user_email = data.get("Email_ID")  # Identify the user by email
        update_data = {
            "FirstName": data.get("FirstName"),
            "LastName": data.get("LastName"),
            "Institution": data.get("Institution"),
            "Class": data.get("Class"),
            "Stream": data.get("Stream"),
            "Specialty": data.get("Specialty"),
        }
        users=models.Table("users","Email_ID","FirstName", "LastName","DOB","Institution","Class","Stream","Specialty")
        result = users.updateMultiple(user_email, update_data)
        if result is not None:   
            return jsonify({"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    




@app.route('/logout',methods=['POST'])
@cross_origin(supports_credentials=True)
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response

@app.route('/signup', methods=['POST'])
@cross_origin(supports_credentials=True)
def signup():
    users = models.Table("users", "Email_ID", "FirstName", "LastName","Password")
    FirstName = request.json['FirstName']
    LastName = request.json['LastName']
    Email_ID = request.json['Email_ID']
    Password = request.json['Password']
    
    # Check if the email already exists in the database
    if users.getone("Email_ID", Email_ID) is not None:
        return jsonify(status="Email already exists")
    
    
    
    # Hash the password using sha256_crypt
    hashed_password = sha256_crypt.hash(Password)
    
    # Insert the new user into the database
    user_data = {
        "FirstName": FirstName,
        "LastName": LastName,
        "Email_ID": Email_ID,
        "Password": hashed_password,
        "user_type":0
    }
    users.insert(user_data)
    
    return jsonify(status="Signup Success!")




@app.route('/insertReport',methods=['POST'])
@cross_origin(supports_credentials=True)
def insert_report():
    token = verify_jwt_token()
    if not token:
        return jsonify(message='Invalid or expired JWT token'), 401
    
    Email_ID = request.json['Email_ID']
    Mood=request.json['MTScore']
    SRQ=request.json['quiz1Score']
    PHQ=request.json['quiz2Score']
    GAD=request.json['quiz3Score']
    now=datetime.now()
    modnow=now.strftime("%Y-%m-%d %H:%M:%S")
    reports=models.Table("reports","Email_ID","Mood","SRQ","PHQ","GAD","Date_and_time")
    report_data={
        "Email_ID":Email_ID,
        "Mood":Mood,
        "SRQ":SRQ,
        "PHQ":PHQ,
        "GAD":GAD,
        "Date_and_time":modnow
    }
    reports.insert(report_data)
    return jsonify("Insertion Succesful")

@app.route('/getReport',methods=['POST'])
@cross_origin(supports_credentials=True)
def getReport():
    token = verify_jwt_token()
    if not token:
        return jsonify(message='Invalid or expired JWT token'), 401
    Email_ID=request.json["Email_ID"]
    reports=models.Table("reports","Email_ID","Mood","SRQ","PHQ","GAD","Date_and_time")
    results=reports.getall("Email_ID",Email_ID)
    return jsonify(results) 
   
@app.route('/getUserDetails',methods=['POST'])
@cross_origin(supports_credentials=True)
def get_User_Details():
    token = verify_jwt_token()
    if not token:
        return jsonify(message='Invalid or expired JWT token'), 401
    Email_ID=request.json["Email_ID"]
    details=models.Table("users","Email_ID","FirstName", "LastName","DOB","Institution","Class","Stream","Specialty")
    results=details.getall("Email_ID",Email_ID)
    return jsonify(results)

@app.route('/getPsy',methods=['POST'])
@cross_origin(supports_credentials=True)
def get_Psy():
    token = verify_jwt_token()
    if not token:
        return jsonify(message='Invalid or expired JWT token'), 401
    psy=models.Table("Psy","id","Name","Rating","Experience","Location","Gender","Degree","Languages","Phone","Fees")
    results=psy.getall("1","1")
    return jsonify(results)

@app.route('/getPost', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_Post():
    # Verify the JWT token for authentication
    token = verify_jwt_token()
    if not token:
        return jsonify(message='Invalid or expired JWT token'), 401

    # Fetch data from the "Blogs" table
    post = models.Table("Blogs", "title", "author", "Publication_date", "tags", "Description", "Subtitle", "Body", "Image")
    results = post.getall("1", "1")
    
    if results is None:
        return jsonify([])
    # Modify the fetched data and create a new list with modified elements
    modified_data = []
    for rs in results:
        if rs[7] is not None:
            image_data = base64.b64decode(rs[7])
            # Perform other modifications to the data as required
            modified_image_data = base64.b64encode(image_data).decode('utf-8')
            modified_tuple = rs[:7] + (modified_image_data,) + rs[8:]  # Create a new tuple with modified data
            modified_data.append(modified_tuple)
        else:
            modified_data.append(rs)

    # Return the modified data as JSON
    return jsonify(modified_data)


@app.route('/putPost',methods=['POST'])
@cross_origin(supports_credentials=True)
def put_Post():
    token = verify_jwt_token()
    if not token:
        return jsonify(message='Invalid or expired JWT token'), 401
    data=request.get_json()
    # print(data)
    #print(request.json)
    post=models.Table("Blogs","Title","Author","Publication_date","tags","Description","Subtitle","Body","Image")
    post_data = {
        "Author": data.get("author"),
        "Publication_date":datetime.today().strftime('%Y-%m-%d'),
        "tags": data.get("tags"),
        "Description": data.get("description"),
        "title":data.get("title"),
        "Subtitle": data.get("subtitle"),
        "Body": data.get("body"),
        "Image": data.get("image")
    }
    post.insert(post_data)
    return jsonify("Blog created successfully")

    


        


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
