from decimal import Decimal

from pydantic import BaseModel, Field


class ProductForm(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    image_url: str = Field(min_length=1)
    weight: str = Field(min_length=1, max_length=80)
    price: Decimal = Field(gt=0)
    features: str = ""
    is_active: bool = True


class LocationForm(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    is_active: bool = True

