from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
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
from typing import Annotated

load_dotenv()
WEB_CLIENT_ID = os.getenv("Client_ID")
SECRET = os.getenv("Client_secret")

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="")

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

# Complete.
def createJWT (user_id: int, email: EmailStr):
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
    }
    proform_jwt_token = jwt.encode(payload, SECRET, algorithm="HS256")
    return proform_jwt_token

# Complete.
def getCurrentUser (token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_session)]):
    try:
        token_data = jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token Expired."
        )
    except jwt.InvalidTokenError:
        raise HTTPException (
            status_code=401,
            detail="Invalid Token."
        )
    user = session.exec(select(Users).where(Users.id == token_data.get("user_id"))).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User Not Found Or Unauthorized User."
        )
    return user


# Endpoints.

# Complete.
@app.get("/profile", status_code=status.HTTP_200_OK, tags=["User - APIs"])
def userProfile (current_user: Annotated[Users, Depends(getCurrentUser)]):
    return current_user

# Complete.
@app.patch("/update-profile", status_code=status.HTTP_200_OK, tags=["User - APIs"])
def updateProfile (items: UpdateProfileItems, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    update_dict = items.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(current_user, key, value)
    
    try:
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
    
    except Exception:
        session.rollback()
        raise HTTPException (
            status_code=500,
            detail="Couldn't Update Profile."
        )
    return current_user

# Complete.
@app.post("/signup", status_code=status.HTTP_201_CREATED, tags=["Authentication - APIs"])
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
                year=items.year,
                linkedin_link=str(items.linkedin_link), 
                github_link=str(items.github_link))

    session.add(user)
    session.commit()
    session.refresh(user)

    unique_name = user.email.split("@")[0]
    public_user_name = PublicUserName(id = user.id, email=user.email, username=unique_name)
    session.add(public_user_name)
    session.commit()
    session.refresh(public_user_name)

    jwt_token = createJWT(user.id, user.email)

    return {
        "message": "Account Successfully Created.",
        "access_token": jwt_token,
        "token_type": "bearer",
    }

# Complete.
@app.post("/auth/google", status_code=status.HTTP_200_OK, tags=["Authentication - APIs"])
def getGoogleTokenId (data: dict, session: Session = Depends(get_session)):
    token = data["token"]
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
            "user_name": user.name,
        }
    else:
        return {
            "message": "Google Token Verified And New User.",
            "is_new_user": True,
            "user_name": id_info["given_name"],
            "user_email": id_info["email"],
        }

# Complete.
@app.get("/get-courses-departments", status_code=status.HTTP_200_OK, tags=["Process - APIs"])
def getCourseDepartment (session: Annotated[Session, Depends(get_session)]):
    data = session.exec(select(AvailableCourseAndDepartments)).all()
    return data

# Complete.
@app.post("/add-course-department", status_code=status.HTTP_201_CREATED, tags=["Admin - APIs"])
def addCourseDepartment (items: AddCourseDepartmentItems, session: Annotated[Session, Depends(get_session)], current_user: Annotated[Users, Depends(getCurrentUser)]):
    is_admin = session.exec(select(Admin).where(Admin.id == current_user.id)).first()
    if not is_admin:
        raise HTTPException (
            status_code=401,
            details="Unauthorized User."
        )
    
    is_course_department_exists_statement = select(AvailableCourseAndDepartments).where(AvailableCourseAndDepartments.course == items.course).where(AvailableCourseAndDepartments.departments == items.department)
    is_course_department_exists = session.exec(is_course_department_exists_statement).first()
    if is_course_department_exists:
        raise HTTPException (
            status_code=400,
            detail="Course And Department Already Exists."
        )
    
    iC = items.course.lower().strip()
    iD = items.department.lower().strip()
    available_course_and_departments = AvailableCourseAndDepartments(course=iC, departments=iD)
   
    try:
        session.add(available_course_and_departments)
        session.commit()
        session.refresh(available_course_and_departments)
    except Exception:
        raise HTTPException (
            status_code=500,
            details="Couldn't Add Course and Department."
        )
    return available_course_and_departments

# Complete.
@app.post("/add-college-domain", status_code=status.HTTP_201_CREATED, tags=["Admin - APIs"])
def addCollegeDomains (items: AddCollegeDomainsItems, current_user: Annotated[Users, Depends(getCurrentUser)], session: Session = Depends(get_session)):
    is_admin = session.exec(select(Admin).where(Admin.id == current_user.id)).first()
    if not is_admin:
        raise HTTPException (
            status_code=401,
            details="Unauthorized User."
        )
    
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

# Progress.
@app.post("/create-project", status_code=status.HTTP_201_CREATED, tags=["Project - APIs"])
def createProject (items: CreateProjectItems, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    is_project_exists_statment = select(Projects).where(Projects.admin == current_user.id)
    is_project_exists = session.exec(is_project_exists_statment).first()
    
    if is_project_exists:
        raise HTTPException (
            status_code=401,
            details="Project Already Exists."
        )
    
    project = Projects(name=items.name, admin=current_user.id, description=items.description, github_link=items.github_link, website_link=items.website_link)
    try:
        session.add(project)
        session.commit()
        session.refresh(project)
    except Exception:
        session.rollback()
        raise HTTPException (
            status_code=500,
            detail="Couldn't Create Project."
        )
    
    return project

# Working."
@app.get("/my-projects", status_code=status.HTTP_200_OK, tags=["Projects - APIs"])
def getMyProjects(current_user: Annotated[Users, Depends(get_session)], session: Annotated[Session, Depends(get_session)]):
    user_projects = session.exec(select(Projects).where(Projects.admin == current_user.id)).all()
    if not user_projects:
        raise HTTPException (
            status_code=400,
            detail="No Created Projects."
        )
    return user_projects


# Progress. Need Frontend.
@app.get("/profile/{username}", status_code=status.HTTP_200_OK, tags=["User - APIs"])
def getPublicProfile (username: str, session: Annotated[Session, Depends(get_session)]):
    is_username_exists = session.exec(select(PublicUserName).where(PublicUserName.username == username)).first()
    if not is_username_exists:
        raise HTTPException (
            status_code=401,
            detail="Invalid Username."
        )
    user = session.exec(select(Users).where(Users.email == is_username_exists.email)).first()
    return user


# aimrrs
