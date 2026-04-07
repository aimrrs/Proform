from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from database import get_session
from pydanticModels import *
from databaseModels import *
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv
import os
import jwt
import datetime

load_dotenv()
WEB_CLIENT_ID = os.getenv("Client_ID")
SECRET = os.getenv("Client_secret")

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://mind-mess-26673378.figma.site",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Progress.
def createJWT (user_id: int, email: EmailStr):
    payload = {
        "user_id": user_id,
        "email": email,
        #"exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
    }
    proform_jwt_token = jwt.encode(payload, SECRET, algorithm="HS256")
    return proform_jwt_token

# Endpoints.

@app.post("/add-college-domain", status_code=status.HTTP_201_CREATED, tags=["Admin - APIs"])
def addCollegeDomains (items: AddCollegeDomainsItems, session: Session = Depends(get_session)):
    domain = items.domain.lower().strip()
    domain_exists = session.exec(select(AvailableColleges).where(AvailableColleges.domains == domain)).first()
    if domain_exists:
        raise HTTPException (
            status_code=400,
            detail="College Domain Already Exisits."
        )

    available_colleges = AvailableColleges(domains=domain)
    try:
        session.add(available_colleges)
        session.commit()
        session.refresh(available_colleges)
    except Exception:
        raise HTTPException (
            status_code=500,
            detail="Couldn't Add College Domain."
        )

    return {
        "message": "College Domain Added.",
        "new_domain": domain,
    }

# Complete.
@app.post("/signup", status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def signUp (items: SignUpItems, session: Session = Depends(get_session)):
    is_user_exist_statement = select(Users.email).where(Users.email == items.email)
    is_user_exists = session.exec(is_user_exist_statement).first()

    if is_user_exists:
        raise HTTPException(
            status_code=400,
            detail="User Already Exists."
        )
    
    user = Users(name=items.name, 
                email=items.email, 
                course=items.course, 
                department=items.department, 
                linkedin_link=str(items.linkedin_link), 
                github_link=str(items.github_link))

    session.add(user)
    session.commit()
    session.refresh(user)

    jwt_token = createJWT(user.id, user.email)

    return {
        "message": "Account Successfully Created.",
        "access_token": jwt_token,
        "token_type": "bearer",
    }

# Complete.
@app.post("/auth/google", status_code=status.HTTP_200_OK, tags=["Authentication"])
def getGoogleTokenId (data: GoogleToken, session: Session = Depends(get_session)):
    print(data)
    token = data#["token"]
    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), WEB_CLIENT_ID)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid Google Token."
        )

    user_domain = id_info["email"].split("@")[-1]

    domains_statement = select(AvailableColleges).where(AvailableColleges.domains == user_domain)
    is_domain_exists = session.exec(domains_statement).first()

    if not is_domain_exists:
        raise HTTPException(
            status_code=401,
            detail="Invalid Email or Email Not Acceptable."
        )
    
    user_statement = select(Users).where(Users.email == id_info["email"])
    user = session.exec(user_statement).first()

    if user:
        jwt_token = createJWT(user.id, user.email)
        return {
            "message": "Google Token Verified and Login Successful.",
            "is_new_user": False,
            "access_token": jwt_token,
            "token_type": "bearer",
        }
    else:
        return {
            "message": "Google Token Verified And New User.",
            "is_new_user": True,
            "user_name": id_info["given_name"],
            "user_email": id_info["email"],
        }

# aimrrs
