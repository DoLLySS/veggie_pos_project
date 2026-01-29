# [NEW] API for Managing Prices
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db, Product

router = APIRouter()

class ProductUpdate(BaseModel):
    price: float

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.put("/products/{name}")
def update_price(name: str, p: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.name == name).first()
    if product:
        product.price = p.price
        db.commit()
        return {"msg": "Updated"}
    return {"msg": "Not found"}