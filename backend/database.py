from mongoengine import connect, Document, StringField, EmailField, IntField


# Database Connection
connect(host="mongodb://localhost:27017/e-kyc")


# MongoEngine User model
class User(Document):
    email = EmailField(required=True, unique=True)
    hashed_password = StringField(required=True)
    level = IntField(required=True)
