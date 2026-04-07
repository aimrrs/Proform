from pydantic import BaseModel, EmailStr, HttpUrl

class SignUpItems (BaseModel):
    name: str
    email: EmailStr
    course: str
    department: str
    year: int
    linkedin_link: HttpUrl | None = None
    github_link: HttpUrl | None = None

class AddCollegeDomainsItems (BaseModel):
    domain: str

class AddCourseDepartmentItems (BaseModel):
    course: str
    department: str

#class GoogleToken (BaseModel):
#    token: str

# aimrrs