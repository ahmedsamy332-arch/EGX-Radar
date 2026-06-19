import requests
import json

API_KEY = "AIzaSyAWP2WRXlIAfGNor8M7_TUHddLBO2syA5o"
PROJECT_ID = "egx-radar"

def to_firestore_value(val):
    if isinstance(val, str):
        return {"stringValue": val}
    elif isinstance(val, bool):
        return {"booleanValue": val}
    elif isinstance(val, int):
        return {"integerValue": str(val)}
    elif isinstance(val, float):
        return {"doubleValue": val}
    elif isinstance(val, list):
        return {"arrayValue": {"values": [to_firestore_value(v) for v in val]}}
    elif isinstance(val, dict):
        return {"mapValue": {"fields": {k: to_firestore_value(v) for k, v in val.items()}}}
    elif val is None:
        return {"nullValue": None}
    else:
        return {"stringValue": str(val)}

def parse_firestore_value(fs_val):
    if "stringValue" in fs_val: return fs_val["stringValue"]
    if "booleanValue" in fs_val: return fs_val["booleanValue"]
    if "integerValue" in fs_val: return int(fs_val["integerValue"])
    if "doubleValue" in fs_val: return float(fs_val["doubleValue"])
    if "arrayValue" in fs_val:
        return [parse_firestore_value(v) for v in fs_val["arrayValue"].get("values", [])]
    if "mapValue" in fs_val:
        return {k: parse_firestore_value(v) for k, v in fs_val["mapValue"].get("fields", {}).items()}
    if "nullValue" in fs_val: return None
    return None

def sign_in(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    r = requests.post(url, json=payload)
    data = r.json()
    if "error" in data:
        raise Exception(data["error"]["message"])
    return data

def sign_up(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    r = requests.post(url, json=payload)
    data = r.json()
    if "error" in data:
        raise Exception(data["error"]["message"])
    return data

def get_user_data(uid, token):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{uid}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    
    if r.status_code == 404:
        return {"favorites": [], "portfolio": []}
        
    data = r.json()
    if "error" in data:
        # Ignore permission issues during initial setup if rules are not set correctly yet, just return empty
        print("Firestore Read Error:", data["error"])
        return {"favorites": [], "portfolio": []}
        
    parsed = {}
    fields = data.get("fields", {})
    for k, v in fields.items():
        parsed[k] = parse_firestore_value(v)
        
    if "favorites" not in parsed: parsed["favorites"] = []
    if "portfolio" not in parsed: parsed["portfolio"] = []
        
    return parsed

def update_user_data(uid, token, data_dict):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{uid}"
    headers = {"Authorization": f"Bearer {token}"}
    
    firestore_fields = {}
    for k, v in data_dict.items():
        firestore_fields[k] = to_firestore_value(v)
        
    payload = {
        "fields": firestore_fields
    }
    
    r = requests.patch(url, headers=headers, json=payload)
    response_data = r.json()
    if "error" in response_data:
        raise Exception(response_data["error"]["message"])
    return True

def refresh_id_token(refresh_token):
    """Use a refresh token to get a new idToken (tokens expire every hour)."""
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    r = requests.post(url, json=payload)
    data = r.json()
    if "error" in data:
        raise Exception(data["error"].get("message", "Token refresh failed"))
    return {
        "idToken": data["id_token"],
        "refreshToken": data["refresh_token"],
        "localId": data["user_id"],
        "email": data.get("email", "")
    }

