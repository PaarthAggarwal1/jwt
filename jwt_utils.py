import datetime
import logging as logger
import secrets
import hashlib
import jwt
from pymongo import MongoClient

from django.conf import settings

class AuthenticationSystem:

    jwt_secret: str

    def __init__(self):
        self.jwt_secret = settings.SECRET_KEY

    def generate_access_token(self, user_details):
        try:
            refresh_token_validity = self.is_refresh_token_valid(user_details["email"], user_details["refresh_token"])
            if not refresh_token_validity["is_successful"]:
                return refresh_token_validity

            payload = {
                "user_email": user_details["email"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),  # Token expires after 1 day
            }

            token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
            return {"is_successful": True, "jwt_token": token, "is_expired": False}
        except Exception as e:
            logger.error(f"Error generating access token: {e}")
            return {"is_successful": False, "error": str(e)}

    def is_jwt_token_valid(self, token):
        try:
            jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

            return {"is_valid": True, "is_expired": False, "is_successful": True}

        except jwt.ExpiredSignatureError:
            return {"is_valid": True, "is_expired": True, "is_successful": False}

        except jwt.InvalidTokenError:
            return {
                "is_valid": False,
                "is_expired": None,
                "is_successful": False,
                "message": "Token is Invalid. Please contact support!!",
            }

    @staticmethod
    def generate_refresh_token():
        refresh_token = secrets.token_urlsafe(32)
        validity_time = (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat()
        return {"refresh_token": refresh_token, "token_validity": validity_time}

    def is_refresh_token_valid(self, email, refresh_token):
        refresh_token_info = self.get_refresh_token_info(email)
        if refresh_token != refresh_token_info.get("refresh_token"):
            return {"is_successful": False, "is_expired": None, "message": "Refresh token is not valid"}

        validity_time = datetime.datetime.fromisoformat(refresh_token_info["token_validity"])
        current_time = datetime.datetime.now()

        if current_time < validity_time:
            return {"is_successful": True, "is_expired": False}

        return {"is_successful": False, "is_expired": True}

    def get_refresh_token_info(self, email):
        try:
            mongo_client = MongoClient('''Enter the Client URL''')
            db = mongo_client['''Enter Database Name''']
            collection = db['''Enter Collection Name''']
            user = collection.find_one({"_id": email})

            refresh_token = user.get("refresh_token")
            refresh_token_validity = user.get("token_validity")

            return {
                "is_successful": True,
                "refresh_token": refresh_token,
                "token_validity": refresh_token_validity,
                "is_token_exists": bool(refresh_token),  # Check if refresh_token exists
            }

        except Exception as e:
            logger.error(f"Error: {e}")
            return {"is_successful": False, "error": str(e)}
