from sqlmodel import SQLModel, Field

class Users (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    course: str
    department: str
    linkedin_link: str | None = None
    github_link: str | None = None

class AvailableColleges (SQLModel, table=True):
    domains: str = Field(index=True, unique=True, primary_key=True)

# aimrrs