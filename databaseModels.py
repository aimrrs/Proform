from sqlmodel import SQLModel, Field

class Users (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    course: str
    department: str
    year: int
    linkedin_link: str | None = None
    github_link: str | None = None

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

# aimrrs