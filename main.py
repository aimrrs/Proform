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

# Complete.
def getUsernameById(user_id: int , session: Annotated[Session, Depends(get_session)]):
    user = session.exec(select(PublicUserName).where(PublicUserName.id == user_id)).first()
    if not user:
        raise HTTPException (
            status_code=404,
            detail="User Not Found."
        )
    return user.username

# Endpoints.

# Complete.
@app.get("/get-projects", status_code=status.HTTP_200_OK, tags=["Discover - APIs"])
def getProjects (sessions: Annotated[Session, Depends(get_session)]):
    projects = sessions.exec(select(Projects).where(Projects.public == True)).all()
    return projects

# Complete.
@app.get("/get-courses-departments", status_code=status.HTTP_200_OK, tags=["Process - APIs"])
def getCourseDepartment (session: Annotated[Session, Depends(get_session)]):
    data = session.exec(select(AvailableCourseAndDepartments)).all()
    return data

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

# Working.
@app.get("/profile/{username}", status_code=status.HTTP_200_OK, tags=["User - APIs"])
def getPublicProfile (username: str, session: Annotated[Session, Depends(get_session)]):
    is_username_exists = session.exec(select(PublicUserName).where(PublicUserName.username == username)).first()
    if not is_username_exists:
        raise HTTPException (
            status_code=404,
            detail="User Not Found."
        )
    user = session.exec(select(Users).where(Users.email == is_username_exists.email)).first()
    projects = []
    for project in user.user_projects:
        if project.public:
            projects.append(project)

    return (user, projects)

# Complete.
@app.delete("/delete-user", status_code=status.HTTP_200_OK , tags=["User - APIs"])
def removeUser (current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    try:
        session.delete(current_user)
        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException (
            status_code=500,
            detail="Couldn't Delete User."
        )
    return {"message": "User Deleted Successfully."}

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
@app.post("/add-course-department", status_code=status.HTTP_201_CREATED, tags=["Admin - APIs"])
def addCourseDepartment (items: AddCourseDepartmentItems, session: Annotated[Session, Depends(get_session)], current_user: Annotated[Users, Depends(getCurrentUser)]):
    is_admin = session.exec(select(Admin).where(Admin.id == current_user.id)).first()
    if not is_admin:
        raise HTTPException (
            status_code=401,
            detail="Unauthorized User."
            
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
            detail="Couldn't Add Course and Department."
        )
    return available_course_and_departments

# Complete.
@app.post("/add-college-domain", status_code=status.HTTP_201_CREATED, tags=["Admin - APIs"])
def addCollegeDomains (items: AddCollegeDomainsItems, current_user: Annotated[Users, Depends(getCurrentUser)], session: Session = Depends(get_session)):
    is_admin = session.exec(select(Admin).where(Admin.id == current_user.id)).first()
    if not is_admin:
        raise HTTPException (
            status_code=401,
            detail="Unauthorized User."
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

# Complete.
@app.post("/create-project", status_code=status.HTTP_201_CREATED, tags=["Project - APIs"])
def createProject (items: CreateProjectItems, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    is_project_exists_statment = select(Projects).where(Projects.admin == current_user.id).where(Projects.name == items.name)
    is_project_exists = session.exec(is_project_exists_statment).first()
    
    if is_project_exists:
        raise HTTPException (
            status_code=400,
            detail="Project Already Exists Or Unauthorized Operation."
        )
    
    project = Projects(name=items.name, admin=current_user.id, description=items.description, github_link=items.github_link, website_link=items.website_link, complete=items.complete, public=items.public)
    try:
        session.add(project)
        session.commit()
        session.refresh(project)

        project_team_link = ProjectTeamLink(project_id=project.id, user_id=project.admin, role="Admin", username=getUsernameById(current_user.id, session=session))
        session.add(project_team_link)
        session.commit()

    except Exception:
        session.rollback()
        raise HTTPException (
            status_code=500,
            detail="Couldn't Create Project."
        )

    return project

# Complete.
@app.get("/my-projects", status_code=status.HTTP_200_OK, tags=["Project - APIs"])
def getMyProjects (current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    user_projects = session.exec(select(Projects).where(Projects.admin == current_user.id)).all()
    if not user_projects:
        raise HTTPException (
            status_code=400,
            detail="No Created Projects."
        )
    return user_projects

# Complete.
@app.patch("/update-my-project", status_code=status.HTTP_201_CREATED, tags=["Project - APIs"])
def updateMyProject (items: UpdateMyProjectItems, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    project = session.exec(select(Projects).where(Projects.admin == current_user.id).where(Projects.id == items.id)).first()
    project_dict = items.model_dump(exclude_unset=True)
    for key, value in project_dict.items():
        if key != "id":
            setattr(project, key, value)
    
    try:
        session.add(project)
        session.commit()
        session.refresh(project)
    except Exception:
        session.rollback()
        raise HTTPException (
            status_code=401,
            detail="Couldn't Update Project."
        )
    return project

# Complete.
@app.get("/projects/{project_id}", status_code=status.HTTP_200_OK, tags=["Project - APIs"])
def getProjectById (project_id: int, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    project = session.exec(select(Projects).where(Projects.id == project_id)).first()
    if not project:
        raise HTTPException (
            status_code=404,
            detail="Project Not Found."
        )
    if not project.admin == current_user.id and current_user not in project.team_members:
        raise HTTPException (
            status_code=403,
            detail="No Permission Access."
        )
    if project.admin == current_user.id:
        info = {"admin": True}
    else:
        info = {"admin": False}
    
    return (project, info)

# Complete.
@app.get("/collab-projects", status_code=status.HTTP_200_OK, tags=["Project - APIs"])
def getCollabProjects (current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    statement = (
        select(Projects)
        .join(ProjectTeamLink)
        .where(ProjectTeamLink.user_id == current_user.id)
        .where(Projects.admin != current_user.id)
    )
    collab_projects = session.exec(statement).all()
    
    if not collab_projects:
        raise HTTPException (
            status_code=404,
            detail="No Project Found."
        )

    return collab_projects

# Complete.
@app.delete("/delete-project", status_code=status.HTTP_200_OK, tags=["project - APIs"])
def deleteProject (project_id: int, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    project = session.exec(select(Projects).where(Projects.id == project_id, Projects.admin == current_user.id)).first()
    if not project:
        raise HTTPException (
            status_code=400,
            detail="Projet Not Found Or Unauthorized Operation."
        )
    try:
        session.delete(project)
        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException (
            status_code=500,
            detail="Couldn't Delete Project."
        )

    return {"message": "Project Deleted Successfully."}

# Complete.
@app.post("/add-team-member", status_code=status.HTTP_201_CREATED, tags=["Team - APIs"])
def addTeamMember (items: AddTeamMemberItems, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    user = session.exec(select(Users).where(Users.id == items.user_id)).first()
    if not user:
        raise HTTPException (
            status_code=404,
            detail="User Not Found."
        )

    project = session.exec(select(Projects).where(Projects.id == items.project_id, Projects.admin == current_user.id)).first()
    if not project:
        raise HTTPException (
            status_code=404,
            detail="Project Not Found."
        )
    
    member = session.exec(select(ProjectTeamLink).where(ProjectTeamLink.user_id == items.user_id, ProjectTeamLink.project_id == items.project_id)).first()
    if member:
        raise HTTPException (
            status_code=400,
            detail="User Exists In Team."
        )
    
    team_member = ProjectTeamLink(project_id=items.project_id, user_id=items.user_id, role=items.role, role_description=items.role_description, username=getUsernameById(items.user_id, session=session))
    try:
        session.add(team_member)
        session.commit()
        session.refresh(team_member)
    except Exception:
        session.rollback()
        raise HTTPException (
            status_code=500,
            detail="Couldn't Add Team Member."
        )
    return team_member

# Complete.
@app.get("/get-team-members", status_code=status.HTTP_200_OK, tags=["Team - APIs"])
def getTeamMember (project_id: int, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    project_team = session.exec(select(ProjectTeamLink).where(ProjectTeamLink.project_id == project_id)).all()
    if not project_team:
        raise HTTPException (
            status_code=404,
            detail="Project Not Found."
        )
    
    is_member = False
    for member in project_team:
        if member.user_id == current_user.id:
            is_member = True
            break
    if not is_member:
        raise HTTPException (
            status_code=401,
            detail="Unauthorized Access."
        )

    return project_team

# Complete.
@app.delete("/delete-team-member", status_code=status.HTTP_200_OK, tags=["Team - APIs"])
def deleteTeamMember (user_id: int, project_id: int, current_user: Annotated[Users, Depends(getCurrentUser)], session: Annotated[Session, Depends(get_session)]):
    project = session.exec(select(Projects).where(Projects.id == project_id, Projects.admin == current_user.id)).first()
    if not project:
        raise HTTPException (
            status_code=404,
            detail="Project Not Found Or Unauthorized."
        )
    team_member = session.exec(select(ProjectTeamLink).where(ProjectTeamLink.user_id == user_id, ProjectTeamLink.project_id == project_id)).first()
    if not team_member:
        raise HTTPException (
            status_code=404,
            detail="Team Member Not Found."
        )
    try:
        session.delete(team_member)
        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException (
            status_code=500,
            detail="Couldn't Delete Team Member."
        )

    return {"message": "Team Member Deleted Successfully."}


# AI
@app.post("/projects/{project_id}/roles", status_code=status.HTTP_201_CREATED, tags=["Application - APIs"])
def createProjectRole(
    project_id: int, 
    items: CreateRoleItems, 
    current_user: Annotated[Users, Depends(getCurrentUser)], 
    session: Annotated[Session, Depends(get_session)]
):
    # 1. Verify project exists and user is admin
    project = session.exec(select(Projects).where(Projects.id == project_id, Projects.admin == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized.")

    # 2. Create the open role
    new_role = ProjectRoles(
        project_id=project.id,
        title=items.title,
        description=items.description
    )
    
    try:
        session.add(new_role)
        session.commit()
        session.refresh(new_role)
    except Exception:
        session.rollback()
        raise HTTPException(status_code=500, detail="Couldn't create role.")
        
    return new_role

@app.post("/roles/{role_id}/apply", status_code=status.HTTP_201_CREATED, tags=["Application - APIs"])
def applyForRole(
    role_id: int, 
    items: ApplyRoleItems, 
    current_user: Annotated[Users, Depends(getCurrentUser)], 
    session: Annotated[Session, Depends(get_session)]
):
    # 1. Verify the role exists and is not filled
    role = session.exec(select(ProjectRoles).where(ProjectRoles.id == role_id)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")
    if role.is_filled:
        raise HTTPException(status_code=400, detail="This role has already been filled.")

    # 2. Check if user already applied to this specific role to prevent spam
    existing_app = session.exec(
        select(Applications).where(Applications.role_id == role_id, Applications.user_id == current_user.id)
    ).first()
    
    if existing_app:
        raise HTTPException(status_code=400, detail="You have already applied for this role.")

    # 3. Create the application
    application = Applications(
        project_id=role.project_id,
        role_id=role.id,
        user_id=current_user.id,
        message=items.message
    )
    
    try:
        session.add(application)
        session.commit()
        session.refresh(application)
    except Exception:
        session.rollback()
        raise HTTPException(status_code=500, detail="Couldn't submit application.")
        
    return {"message": "Application submitted successfully!"}

@app.patch("/applications/{application_id}/status", status_code=status.HTTP_200_OK, tags=["Application - APIs"])
def updateApplicationStatus(
    application_id: int, 
    items: ApplicationStatusItems, 
    current_user: Annotated[Users, Depends(getCurrentUser)], 
    session: Annotated[Session, Depends(get_session)]
):
    # 1. Fetch the application
    application = session.exec(select(Applications).where(Applications.id == application_id)).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    # 2. Verify the current_user is the Admin of the project this application belongs to
    project = session.exec(select(Projects).where(Projects.id == application.project_id)).first()
    if not project or project.admin != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized. Only the project admin can do this.")

    # 3. Update the application status
    new_status = items.status.lower()
    if new_status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'rejected'.")
        
    application.status = new_status
    session.add(application)

    # 4. THE MAGIC: If accepted, do the extra database work
    if new_status == "accepted":
        # A. Mark the role as filled
        role = session.exec(select(ProjectRoles).where(ProjectRoles.id == application.role_id)).first()
        if role:
            role.is_filled = True
            session.add(role)
            
        # B. Add them to the actual ProjectTeamLink table!
        team_link = ProjectTeamLink(
            project_id=project.id,
            user_id=application.user_id,
            role=role.title if role else "Member",
            role_description="Added via application."
        )
        session.add(team_link)

    # 5. Save everything at once
    try:
        session.commit()
        session.refresh(application)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Database error while processing application.")

    return {"message": f"Application successfully marked as {new_status}.", "application": application}


# aimrrs
