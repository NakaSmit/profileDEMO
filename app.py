from flask import Flask, jsonify, request
import os
import firebase_admin
from firebase_admin import credentials, firestore
from supabase import create_client, Client
import uuid


app = Flask(__name__)

# Use the environment variable instead of hardcoding the file path
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS","serviceAccountKey.json")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Supabase
SUPABASE_URL = "https://ydpuhzopboechregfhti.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlkcHVoem9wYm9lY2hyZWdmaHRpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc5MDU1NjMsImV4cCI6MjA1MzQ4MTU2M30.aPJzxA8l2SoX3mYGWhIc49pstdYjbLXMtBDHVfcJFwU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
@app.route("/post/<p_ID>/<description>/<post>", methods=["GET"])
def create_posts(p_ID,description,post):
    data = db.collection("Users").document(p_ID).get().to_dict()

    # Get the post count dynamically
    post_collection_ref = db.collection(f"Users/{p_ID}/Post")
    count_query = post_collection_ref.count()
    count_snapshot = count_query.get()

    # Extract count properly
    # request_data = request.get_json() or {}
    post_number = count_snapshot[0][0].value -1 if count_snapshot else -1 
    # bio = request_data.get("bio", "Default Bio")
    # post_photo = request_data.get("post_photo", "unset")
    link = request.args.get('link')

    if not link:
            return jsonify({"error": "Missing link parameter"}), 400

        # Firestore update
    # Create post with a dynamic ID (incremented)
    post_id = post_number + 1
    post_ref = post_collection_ref.document(str(int(post_id)))  # Convert to string for Firestore ID

    post_ref.set({
        "uid":  post_id,
        post: link,
        "description": description,
    })

    return jsonify({"message": "Post successfully", "post_id": int(post_id)}),200


#Create Profile    
# @app.route("/create-default-profile/<p_ID>", methods=["GET"])
def create_default_profile(p_ID):
    #photo_type=False(supabase)  
    #photo_type=True(firebase)      
    data = db.collection("Users").document(p_ID).get().to_dict()
    

    colleges = data.get("colleges", [])  # Expected format: [{"college_name": "SBMP", "college_semORyr": "6-3"}, {...}]
    if not colleges:
        colleges = [{"college_name": "unset", "college_semORyr": "unset"}]
    pText = { 
        "display_name": data.get("display_name"),
        "p_email":data.get("email"),
        "uid": data.get("uid"),
        # "display_name":"name",
        # "p_email":"emaol",
        # "uid":"dsfv",
        "phone_No": "unset",
        "user_class":"unset",
        "bio": "unset",
        "college_name" : "unset",
        "college_semORyr": "unset",
        "GitHub":"unset",
        "Likedin":"unset",
        "YouTube":"unset",
        "Instagram":"unset",
    }
    pPhoto={
        # "profile_type":p_type,
        # "banner_type":b_type,
        # "profile_url":data.get("p_url"),
        # "banner_url":data.get("b_url")
        "profile_url":"unset",
        "banner_url":"unset",
        "photo_type":"",
        "banner_type":"",
        "file":""
        
    }
    postText={
        "description": "",
        "image":"",
    }

    createFire(f"Users/{p_ID}/Post",postText)
    createFire(f"Users/{p_ID}/Profile",pText,"p_text")
    createFire(f"Users/{p_ID}/Profile",pPhoto,"p_photo")
    
    return jsonify({"p_text":pText, "p_photo":pPhoto }),200

#Edit Profile  
@app.route("/edit-default-profile/<p_ID>/<display_name>/<uid>/<user_class>/<p_bio>/<college_name>/<college_semORyr>/<photo_url>/<posts>", methods=["GET"])
#@app.route("/edit-default-profile/<p_ID>/<display_name>/<email>/<uid>/<p_phone>/<user_class>/<p_bio>", methods=["GET"])

def edit_default_profile(p_ID,user_class,p_bio,college_name,college_semORyr,display_name,uid,photo_url,p_url,b_url,posts):
    #photo_type=False(supabase)  
    #photo_type=True(firebase)  
    photo_type=False

    pText= { 
        "display_name": display_name,
       # "p_email":email,
        "uid": uid,
        #"phone_No": p_phone,
        "user_class": user_class,
        "bio": p_bio,
        "college_name" : college_name,
        "college_semORyr": college_semORyr,
    }
    pPhoto={
        "photo_type":photo_type,
        "photo_url": photo_url,
        "profile_type":p_type,
        "banner_type":b_type,
        "profile_url":p_url,
        "banner_url":b_url
    }
    
    createFire(f"Users/{p_ID}/Profile",pText,"p_text")
    createFire(f"Users/{p_ID}/Profile",pPhoto,"p_photo")
    
    return jsonify({"p_text":pText, "p_photo":pPhoto }),200
@app.route('/upload/files', methods=['POST'])
def upload_filess():
    BUCKET_NAME = "images"
    FOLDER_NAME = request.form.get('FOLDER_NAME')
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = f"{FOLDER_NAME}/{file_name}"
    
    try:
        response = supabase.storage.from_(BUCKET_NAME).upload(file_path, file.read(), {'content-type': file.content_type})
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path}"
        return jsonify({"message": "File uploaded successfully", "url": public_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#EDIT Profile Image
@app.route("/edit-profile-image/<p_ID>/<path:photo_url>", methods=["GET","POST"])
def edit_profile_image(p_ID, photo_url):
    if "http" in photo_url:
        # Directly store in Firebase if it's already a URL
        pPhoto = {
            "photo_type": True,
            "profile_url": photo_url
        }
        createFire(f"Users/{p_ID}/Profile", pPhoto, "p_photo")
        return jsonify({"message": "Profile image updated from URL", "p_photo": pPhoto}), 200
    else:
        # Check if an image file is provided
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        image = request.files['image']
        filename = image.filename
        temp_path = os.path.join("temp_uploads", filename)

        try:
            # Create temp directory if not exists
            os.makedirs("temp_uploads", exist_ok=True)
            
            # Save the file temporarily
            image.save(temp_path)

            # Upload the saved file to Supabase
            with open(temp_path, "rb") as file:
                response = supabase.storage.from_("profile").upload(
                    file=file,
                    path=f"pro/{filename}",
                    file_options={"cache-control": "3600", "upsert": "false"}
                )

            # Delete the temp file after upload
            os.remove(temp_path)

            if not response:
                return jsonify({"error": "Upload to Supabase failed"}), 500

            # Get public URL
            public_url = supabase.storage.from_("profile").get_public_url(f"pro/{filename}")

            # Store in Firebase
            pPhoto = {
                "photo_type": False,
                "profile_url": public_url
            }
            createFire(f"Users/{p_ID}/Profile", pPhoto, "p_photo")

            return jsonify({"message": "Profile image uploaded & updated", "p_photo": pPhoto}), 200

        except Exception as e:
             return jsonify({"error": str(e)}), 500


@app.route("/edit-profile-banner/<p_ID>/<path:banner_url>", methods=["GET","POST"])
def edit_profile_banner(p_ID, banner_url):
    if "http" in banner_url:
        # Directly store in Firebase if it's already a URL
        pPhoto = {
            "photo_type": True,
            "banner_url": banner_url
        }
        createFire(f"Users/{p_ID}/Profile", pPhoto, "p_photo")
        return jsonify({"message": "Profile image updated from URL", "p_photo": pPhoto}), 200
    else:
        # Check if an image file is provided
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        image = request.files['image']
        filename = image.filename
        temp_path = os.path.join("temp_uploads", filename)

        try:
            # Create temp directory if not exists
            os.makedirs("temp_uploads", exist_ok=True)
            
            # Save the file temporarily
            image.save(temp_path)

            # Upload the saved file to Supabase
            with open(temp_path, "rb") as file:
                response = supabase.storage.from_("profile").upload(
                    file=file,
                    path=f"banner/{filename}",
                    file_options={"cache-control": "3600", "upsert": "false"}
                )

            # Delete the temp file after upload
            os.remove(temp_path)

            if not response:
                return jsonify({"error": "Upload to Supabase failed"}), 500

            # Get public URL
            public_url = supabase.storage.from_("profile").get_public_url(f"banner/{filename}")

            # Store in Firebase
            pPhoto = {
                "photo_type": False,
                "banner_url": public_url
            }
            createFire(f"Users/{p_ID}/Profile", pPhoto, "p_photo")

            return jsonify({"message": "Profile image uploaded & updated", "p_photo": pPhoto}), 200

        except Exception as e:
             return jsonify({"error": str(e)}), 500


@app.route("/edit-post/<p_ID>/<platform>", methods=["GET"])
def edit_post(p_ID,platform):
    try:
        link = request.args.get('link')

        if not link:
            return jsonify({"error": "Missing link parameter"}), 400

        # Firestore update
        pPhoto = {platform: link}
        success = createFire(f"Users/{p_ID}/Post", pPhoto, "jaze3ZCduzcBvfqfIXlw")

        if not success:
            return jsonify({"error": "Failed to update Firestore"}), 500

        return jsonify({
            "message": f"{platform} link updated successfully",
            "updated_link": link,
            "p_text": pPhoto
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to update link: {str(e)}"}), 500
         
@app.route("/edit-pImage/<p_ID>/<platform>", methods=["GET"])
def edit_pImage(p_ID,platform):
    try:
        link = request.args.get('link')

        if not link:
            return jsonify({"error": "Missing link parameter"}), 400

        # Firestore update
        pPhoto = {platform: link}
        success = createFire(f"Users/{p_ID}/Profile", pPhoto, "p_photo")

        if not success:
            return jsonify({"error": "Failed to update Firestore"}), 500

        return jsonify({
            "message": f"{platform} link updated successfully",
            "updated_link": link,
            "p_text": pPhoto
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update link: {str(e)}"}), 500

#CREATE LINKS
@app.route('/edit-link/<p_ID>/<platform>', methods=['GET'])
def update_link(p_ID, platform):
    try:
        link = request.args.get('link')

        if not link:
            return jsonify({"error": "Missing link parameter"}), 400

        # Firestore update
        pText = {platform: link}
        success = createFire(f"Users/{p_ID}/Profile", pText, "p_text")

        if not success:
            return jsonify({"error": "Failed to update Firestore"}), 500

        return jsonify({
            "message": f"{platform} link updated successfully",
            "updated_link": link,
            "p_text": pText
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update link: {str(e)}"}), 500


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

        #if "http"  in p_photo.get("photo_url"): photo_type = True

        return jsonify({"p_text":p_text, "p_photo":p_photo }),200
    else:
        return create_default_profile(p_ID),200

@app.route("/get-Roles/<p_ID>/<college_id>")
def get_Roles(p_ID,college_id):
    college_Roles= db.collection(f"Users/{p_ID}/Profile/p_text/collegeRoles").document(college_id).get().to_dict().get("Roles")
    return college_Roles,200

@app.route("/get-link/<p_ID>",methods=["GET"])
def fetch_link(p_ID):
    links_ref = db.collection(f"Users/{p_ID}/Profile/p_text/Links").stream()
    links = {}
    for doc in links_ref:
        links.update(doc.to_dict())  # Merge all documents
    return jsonify({"links": links}), 200
if __name__ == "__main__":
    app.run(debug=True)
