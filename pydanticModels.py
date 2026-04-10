from pydantic import BaseModel, EmailStr, HttpUrl

class SignUpItems(BaseModel):
    name: str
    email: EmailStr
    course: str
    department: str
    year: int
    linkedin_link: HttpUrl | None = None
    github_link: HttpUrl | None = None

class AddCollegeDomainsItems(BaseModel):
    domain: str

class AddCourseDepartmentItems(BaseModel):
    course: str
    department: str

class UpdateProfileItems(BaseModel):
    year: int | None = None
    linkedin_link: str | None = None
    github_link: str | None = None

class CreateProjectItems(BaseModel):
    name: str
    admin: int
    description: str | None = None
    github_link: str
    website_link: str | None = None
    complete: bool
    public: bool

class UpdateMyProjectItems(BaseModel):
    id: str
    name: str | None = None
    description: str | None = None
    github_link: str | None = None
    website_link: str | None = None
    complete: bool | None = None
    public: bool | None = None

class AddTeamMemberItems(BaseModel):
    user_id: int
    project_id: int
    role: str
    role_description: str | None = None

class CreateRoleItems(BaseModel):
    title: str
    description: str

class ApplyRoleItems(BaseModel):
    message: str

class ApplicationStatusItems(BaseModel):
    status: str


#class GoogleToken (BaseModel):
#    token: str

# aimrrs