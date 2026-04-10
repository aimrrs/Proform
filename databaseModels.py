from sqlmodel import SQLModel, Field, Relationship
from typing import List

class ProjectTeamLink (SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    project_id: int = Field(foreign_key="projects.id", primary_key=True, ondelete="CASCADE")
    role: str
    role_description: str | None = None
    username: str

class Users (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    course: str
    department: str
    year: int
    linkedin_link: str | None = None
    github_link: str | None = None
    user_projects: List["Projects"] = Relationship(back_populates="team_members", link_model=ProjectTeamLink)

class Projects (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    admin: int = Field(index=True, foreign_key="users.id", ondelete="CASCADE")
    description: str | None = None
    github_link: str | None = None
    website_link: str | None = None
    complete: bool
    public: bool
    open_roles: List["ProjectRoles"] = Relationship()
    team_members: List["Users"] = Relationship(back_populates="user_projects", link_model=ProjectTeamLink)

class AvailableColleges (SQLModel, table=True):
    domains: str = Field(index=True, unique=True, primary_key=True)

class AvailableCourseAndDepartments (SQLModel, table=True):
    course: str = Field(index=True, primary_key=True)
    departments: str = Field(index=True)

class Admin (SQLModel, table=True):
    id: int = Field(primary_key=True, foreign_key="users.id", ondelete="CASCADE")

class PublicUserName (SQLModel, table=True):
    id: int = Field(primary_key=True, foreign_key="users.id", ondelete="CASCADE")
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)

class ProjectRoles(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", ondelete="CASCADE")
    title: str
    description: str
    is_filled: bool = Field(default=False)

class Applications(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # Linking to the project makes fetching all applications for an admin much faster
    project_id: int = Field(foreign_key="projects.id", ondelete="CASCADE") 
    role_id: int = Field(foreign_key="projectroles.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE")
    message: str
    status: str = Field(default="pending")


# aimrrs