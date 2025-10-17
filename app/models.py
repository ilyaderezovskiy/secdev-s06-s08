
from pydantic import BaseModel, constr, field_validator
from typing import Optional
import re

# Строгие типы для валидации
Username = constr(
    strip_whitespace=True, 
    min_length=3, 
    max_length=48, 
    pattern=r"^[a-zA-Z0-9_.-]+$"
)
Password = constr(min_length=8, max_length=128)  # Увеличиваем min_length для безопасности

class LoginRequest(BaseModel):
    username: Username
    password: Password
    
    @field_validator('username')
    @classmethod
    def validate_username_complexity(cls, v):
        """Дополнительная валидация username"""
        if v.startswith('.') or v.endswith('.'):
            raise ValueError('Username cannot start or end with a dot')
        if '..' in v:
            raise ValueError('Username cannot contain consecutive dots')
        if v.lower() in ['admin', 'root', 'system']:
            raise ValueError('This username is not allowed')
        return v
    
    @field_validator('password')
    @classmethod 
    def validate_password_complexity(cls, v):
        """Дополнительная валидация пароля"""
        if v.isnumeric():
            raise ValueError('Password must contain letters')
        if v.isalpha():
            raise ValueError('Password must contain numbers')
        if v.lower() == v:
            raise ValueError('Password must contain uppercase letters')
        return v

class Item(BaseModel):
    id: int
    name: str = constr(min_length=1, max_length=100)  # Добавляем ограничения и для Item
    description: Optional[str] = constr(max_length=500)  # Ограничение длины описания
