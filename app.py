from flask import Flask, jsonify, request
import os
import firebase_admin
from firebase_admin import credentials, firestore
from supabase import create_client, Client


app = Flask(__name__)

# Use the environment variable instead of hardcoding the file path
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS","serviceAccountKey.json")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Supabase
SUPABASE_URL = "https://jgaapanxbjpbduxamlgf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpnYWFwYW54YmpwYmR1eGFtbGdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxMTY5OTYsImV4cCI6MjA1NzY5Mjk5Nn0.8k2g2dryfGuS7DgbUQmmN4at_gXxNKYCvxs4EFxf0yEy"
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
    colleges = data.get("colleges", [])  # Expected format: [{"college_name": "SBMP", "college_semORyr": "6-3"}, {...}]
    if not colleges:
        colleges = [{"college_name": "unset", "college_semORyr": "unset"}]
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
@app.route("/edit-default-profile/<p_ID>/<display_name>/<uid>/<user_class>/<p_bio>/<college_name>/<college_semORyr>/<photo_url>/<posts>", methods=["GET"])
#@app.route("/edit-default-profile/<p_ID>/<display_name>/<email>/<uid>/<p_phone>/<user_class>/<p_bio>", methods=["GET"])

def edit_default_profile(p_ID,user_class,p_bio,college_name,college_semORyr,display_name,uid,photo_url,posts):
    #photo_type=False(supabase)  
    #photo_type=True(firebase)  
    photo_type=False
    if "http"  in photo_url: photo_type = True

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
    }
    
    createFire(f"Users/{p_ID}/Profile",pText,"p_text")
    createFire(f"Users/{p_ID}/Profile",pPhoto,"p_photo")
    
    return jsonify({"p_text":pText, "p_photo":pPhoto }),200




# Upload endpoint
#supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/upload/images', methods=['POST'])
def upload_to_supabase(p_ID):
    BUCKET_NAME = "profile"
    folder_path = request.form.get('folder')  # Expecting 'folder=banner'

    files = request.files.getlist('files')
    user_id = request.form.get('user_id')  # Expecting user_id from request


    if not folder_path or not files:
        return jsonify({"error": "Missing folder path or files"}), 400

    uploaded_urls = []

    for file in files:
        try:
            file_path = f"{folder_path}/{file.filename}"

            # Upload to Supabase
            res = supabase.storage.from_(BUCKET_NAME).upload(file_path, file, {"content-type": file.content_type})
            public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
            uploaded_urls.append(public_url)

            # Update Firestore banner_url
            # Store in Firestore using createFire
            pPhoto = {"banner_url": uploaded_urls}
            createFire(f"Users/{p_ID}/Profile", pPhoto, "p_photo")

        except Exception as e:
            return jsonify({"error": f"Failed to upload {file.filename}", "details": str(e)}), 500

    return jsonify({"message": "Banner image uploaded & updated", "p_photo": pPhoto}), 200



#EDIT Profile Image
@app.route("/edit-profile-image/<p_ID>/<path:photo_url>", methods=["GET","POST"])
def edit_profile_image(p_ID, photo_url):
    if "http" in photo_url:
        # Directly store in Firebase if it's already a URL
        pPhoto = {
            "photo_type": True,
            "photo_url": photo_url
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
                "photo_url": public_url
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
         
         
#CREATE LINKS
@app.route("/create-link/<p_ID>",methods=["GET"])
def create_link(p_ID):
    try:
        # Extract all query parameters
        data = request.args.to_dict()

        if not data:
            return jsonify({"error": "No links provided"}), 400

        # Add links to Firestore under 'Links' collection
        doc_ref = db.collection(f"Users/{p_ID}/Profile/p_text/Links").document()
        doc_ref.set(data, merge=True)
       # createFire(f"Users/{p_ID}/Profile",pText,"p_text")


        return jsonify({"message": "Links added successfully", "data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
