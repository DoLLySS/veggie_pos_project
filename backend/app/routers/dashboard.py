from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db, Transaction
from datetime import date

router = APIRouter()

@router.get("/daily")
def get_daily_sales(db: Session = Depends(get_db)):
    today = date.today()
    total = db.query(func.sum(Transaction.total_amount)).filter(func.date(Transaction.timestamp) == today).scalar() or 0
    count = db.query(Transaction).filter(func.date(Transaction.timestamp) == today).count()
    recent = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(5).all()
    return {
        "total_sales": total, "transaction_count": count,
        "recent_txns": [{"id": t.id, "time": t.timestamp, "amount": t.total_amount, "cashier": t.cashier_name} for t in recent]
    }