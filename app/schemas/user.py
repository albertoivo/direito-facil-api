from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    nome: str
    email: str


class UserCreate(UserBase):
    nome: str
    email: str
    password: str
    role: Optional[str] = "user"


class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = Field(None, pattern=r"^(user|admin)$")

    @field_validator("nome")
    def nome_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Nome não pode ser vazio")
        return v.strip() if v else v

    @field_validator("email")
    def email_lowercase(cls, v):
        return v.lower() if v else v


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str = "user"
