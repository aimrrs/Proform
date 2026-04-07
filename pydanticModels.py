from pydantic import BaseModel, EmailStr, HttpUrl

class SignUpItems (BaseModel):
    name: str
    email: EmailStr
    course: str
    department: str
    year: str
    linkedin_link: HttpUrl | None = None
    github_link: HttpUrl | None = None

class AddCollegeDomainsItems (BaseModel):
    domain: str

#class GoogleToken (BaseModel):
#    token: str

# aimrrs