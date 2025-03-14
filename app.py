from flask import Flask, jsonify, request
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Use the environment variable instead of hardcoding the file path
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS","serviceAccountKey.json")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/")
def home():
    return jsonify({"message": "Firebase API is working"}), 200

def createFire(collection_path, data, documentName=False):
    
    # Add the document to Firestore
    if documentName:
        doc_ref = db.collection(collection_path).document(documentName)
    else:
        doc_ref = db.collection(collection_path).document()
    doc_ref.set(data,merge=True)
    return doc_ref


#ROLES
@app.route("/create-Roles/<p_ID>", methods=["GET"])
def create_Roles(p_ID):
    data = db.collection("Users").document(p_ID).get().to_dict()
    colleges = db.collection(f"Users/{p_ID}/UserColleges").stream()
    c=[]
    ids = []
    for college in colleges:
        createFire(f"Users/{p_ID}/Profile/p_text/collegeRoles",{
            "Roles":college.get("Roles"),
            "Name": college.get("CollegeName")
        }, college.id)
        c.append(college.get("CollegeName"))
        ids.append(college.id)
    
    createFire(f"Users/{p_ID}/Profile",{
        "collegeList": c,
        "collegeIdList": ids
        
    },"p_text")
    return {"colleges":c, "collegeIDs": ids},200
    

#Create Post
@app.route("/post/<p_ID>", methods=["GET"])
def create_posts(p_ID):
    data = db.collection("Users").document(p_ID).get().to_dict()

    # Get the post count dynamically
    post_collection_ref = db.collection(f"Users/{p_ID}/Profile/p_photo/posts")
    count_query = post_collection_ref.count()
    count_snapshot = count_query.get()

    # Extract count properly
    post_number = count_snapshot[0][0].value -1 if count_snapshot else -1  

    # Create post with a dynamic ID (incremented)
    post_id = post_number + 1
    post_ref = post_collection_ref.document(str(int(post_id)))  # Convert to string for Firestore ID

    post_ref.set({
        "display_name": data.get("display_name"),
        "uid": data.get("uid"),
        "post_photo": "unset",
        "bio": "SAHIR",
    })

    return jsonify({"message": "Post successfully", "post_id": int(post_id)}),200


#Create Profile    
#@app.route("/create-default-profile/<p_ID>", methods=["GET"])
def create_default_profile(p_ID):
    #photo_type=False(supabase)  
    #photo_type=True(firebase)      
    photo_type=False

    data = db.collection("Users").document(p_ID).get().to_dict()
    if "http"  in data.get("photo_url"): photo_type = True

    pText = { 
        "display_name": data.get("display_name"),
        "p_email":data.get("email"),
        "uid": data.get("uid"),
        "phone_No": "unset",
        "user_class":"unset",
        "bio": "unset",
        "college_name" : "unset",
        "college_semORyr": "unset",
    }
    pPhoto={
        "photo_type":photo_type,
        "profile_url":data.get("photo_url"),    
    }
    # roles={
    #     "Roles":data.get("Roles")
    # }


    createFire(f"Users/{p_ID}/Profile",pText,"p_text")
    createFire(f"Users/{p_ID}/Profile",pPhoto,"p_photo")
    
    
    return jsonify({"p_text":pText, "p_photo":pPhoto }),200

#Edit Profile  
@app.route("/edit-default-profile/<p_ID>/<display_name>/<email>/<uid>/<p_phone>/<user_class>/<p_bio>/<college_name>/<college_semORyr>/<photo_url>/<posts>", methods=["GET"])
#@app.route("/edit-default-profile/<p_ID>/<display_name>/<email>/<uid>/<p_phone>/<user_class>/<p_bio>", methods=["GET"])
def edit_default_profile(p_ID,p_phone,user_class,p_bio,college_name,college_semORyr,display_name,email,uid,photo_url,posts):
    #photo_type=False(supabase)  
    #photo_type=True(firebase)  
    photo_type=False
    if "http"  in photo_url: photo_type = True

    pText= { 
        "display_name": display_name,
        "p_email":email,
        "uid": uid,
        "phone_No": p_phone,
        "user_class": user_class,
        "bio": p_bio,
        "college_name" : college_name,
        "college_semORyr": college_semORyr,
    }
    pPhoto={
        "photo_type":photo_type,
        "profile_url": photo_url,
    }
    
    createFire(f"Users/{p_ID}/Profile",pText,"p_text")
    createFire(f"Users/{p_ID}/Profile",pPhoto,"p_photo")
    
    
    return jsonify({"p_text":pText, "p_photo":pPhoto }),200


# Fetch Profile

#http://127.0.0.1:5000/fetch-profile/VIc9yUl80yfQoSYcoesyWozVBVa2
@app.route("/fetch-profile/<p_ID>", methods=["GET"])

def fetch_profile(p_ID):
    #photo_type=False(supabase)  
    #photo_type=True(firebase)  

    docs = db.collection(f"Users/{p_ID}/Profile").limit(1).stream()
    
    if any (docs):
        
        p_text = db.collection(f"Users/{p_ID}/Profile").document("p_text").get().to_dict()
        p_photo = db.collection(f"Users/{p_ID}/Profile").document("p_photo").get().to_dict()

        if "http"  in p_photo.get("photo_url"): photo_type = True

        return jsonify({"p_text":p_text, "p_photo":p_photo }),200
    else:
        return create_default_profile(p_ID),200

@app.route("/get-Roles/<p_ID>/<college_id>")
def get_Roles(p_ID,college_id):
    college_Roles= db.collection(f"Users/{p_ID}/Profile/p_text/collegeRoles").document(college_id).get().to_dict().get("Roles")
    return college_Roles,200


if __name__ == "__main__":
    app.run(debug=True)
