from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/")
def home():
    return jsonify({"message": "Firebase API is working"}), 200

# Fetch All Profiles
@app.route("/profiles", methods=["GET"])
def get_profiles():
    profiles = db.collection("Profile").stream()
    data = []
    for profile in profiles:
        profile_dict = profile.to_dict()
        profile_dict["id"] = profile.id
        
        # Fetch Sub Collections (Posts)
        posts = db.collection("Profile").document(profile.id).collection("Posts").stream()
        post_list = []
        for post in posts:
            post_dict = post.to_dict()
            post_dict["id"] = post.id

            # Fetch Sub Collections (Comments)
            comments = db.collection("Profile").document(profile.id).collection("Posts").document(post.id).collection("comments").stream()
            comment_list = []
            for comment in comments:
                comment_dict = comment.to_dict()
                comment_dict["id"] = comment.id

                # Fetch Sub Comments
                sub_comments = db.collection("Profile").document(profile.id).collection("Posts").document(post.id).collection("comments").document(comment.id).collection("sub_comments").stream()
                sub_comment_list = [sub_comment.to_dict() for sub_comment in sub_comments]
                comment_dict["sub_comments"] = sub_comment_list

                comment_list.append(comment_dict)

            post_dict["comments"] = comment_list
            post_list.append(post_dict)

        profile_dict["posts"] = post_list
        data.append(profile_dict)
    return jsonify(data), 200

# Add Profile
@app.route("/profile", methods=["POST"])
def add_profile():
    body = request.json
    ref = db.collection("Profile").add(body)
    return jsonify({"id": ref[1].id, "message": "Profile added successfully"}), 201

# Update Profile
@app.route("/profile/<profile_id>", methods=["PUT"])
def update_profile(profile_id):
    body = request.json
    db.collection("Profile").document(profile_id).update(body)
    return jsonify({"message": "Profile updated successfully"}), 200

# Delete Profile
@app.route("/profile/<profile_id>", methods=["DELETE"])
def delete_profile(profile_id):
    db.collection("Profile").document(profile_id).delete()
    return jsonify({"message": "Profile deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
