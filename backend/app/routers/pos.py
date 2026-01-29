from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..services import hardware, ai_service
from ..database import get_db, Transaction, TransactionItem, Product

router = APIRouter()

@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    data = hardware.get_weight_data()
    # Fetch Real-time prices from DB
    products = db.query(Product).all()
    prices = {p.name: p.price for p in products}
    return {**data, "prices": prices}

@router.post("/predict")
def predict(file: UploadFile = File(...)):
    res = ai_service.predict_image()
    return {"result": res}

class CartItem(BaseModel):
    name: str
    weight: float
    price: float
    qty: int
    total: float

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    total: float
    cashier: str

@router.post("/checkout")
def checkout(req: CheckoutRequest, db: Session = Depends(get_db)):
    txn = Transaction(total_amount=req.total, cashier_name=req.cashier)
    db.add(txn)
    db.commit()
    db.refresh(txn)
    for item in req.items:
        db.add(TransactionItem(
            transaction_id=txn.id, product_name=item.name, weight=item.weight,
            price_per_unit=item.price, quantity=item.qty, total_price=item.total
        ))
    db.commit()
    return {"msg": "Saved", "txn_id": txn.id}