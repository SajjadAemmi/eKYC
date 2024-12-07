from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import jwt
from tasks import face_verification, speech_to_text, gesture_recognition
from tasks import celery_app
from database import User


app = FastAPI()


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = "your_secret_key"


# Pydantic models for requests and responses
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# Utility functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(datetime.timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")


def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )
    token = authorization.split(" ")[1]
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email


@app.post("/signup", status_code=201)
def signup(request: SignUpRequest):
    if User.objects(email=request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed_password = get_password_hash(request.password)
    User(email=request.email, hashed_password=hashed_password, level=1).save()
    return {"message": "User registered successfully."}


@app.post("/signin", response_model=TokenResponse)
def signin(request: SignInRequest):
    user = User.objects(email=request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    access_token = create_access_token(data={"email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/signout")
def signout(token: str = Depends(decode_access_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return {"message": "Sign-out successful."}


@app.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {
        "message": f"Hello, {current_user}. You have access to this protected route."
    }


@app.get("/profile")
def profile(current_user: str = Depends(get_current_user)):
    user = User.objects(email=current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"email": user.email, "message": "This is your profile."}


@app.post("/auth/face")
async def auth_face(file: UploadFile):
    task = face_verification.delay(await file.read())
    return {"task_id": task.id, "status": "processing"}


@app.post("/auth/speech")
async def auth_speech(file: UploadFile):
    task = speech_to_text.delay(await file.read())
    return {"task_id": task.id, "status": "processing"}


@app.post("/auth/gesture")
async def auth_gesture(file: UploadFile, current_user: str = Depends(get_current_user)):
    task = gesture_recognition.delay(await file.read())
    return {"task_id": task.id, "status": task.state}


@app.get("/task_status/{task_id}")
def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "SUCCESS":
        return {"status": "completed", "result": result.result}
    else:
        print(result.state)
        return {"status": "failed"}
