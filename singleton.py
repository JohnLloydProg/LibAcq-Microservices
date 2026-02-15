from firebase import Firebase

firebase_singleton:Firebase = None

def get_firebase() -> Firebase:
    global firebase_singleton
    if not firebase_singleton:
        firebase_singleton = Firebase(cred_path='./credentials.json')
    return firebase_singleton