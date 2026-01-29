import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "postgresql://admin:securepassword@db/veggie_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

# [NEW] Product Table for Dynamic Pricing
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    price = Column(Float)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float)
    cashier_name = Column(String)
    items = relationship("TransactionItem", back_populates="transaction")

class TransactionItem(Base):
    __tablename__ = "transaction_items"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    product_name = Column(String)
    weight = Column(Float)
    price_per_unit = Column(Float)
    quantity = Column(Integer)
    total_price = Column(Float)
    transaction = relationship("Transaction", back_populates="items")

def init_db():
    Base.metadata.create_all(bind=engine)
    # Seed Initial Products if empty
    db = SessionLocal()
    if db.query(Product).count() == 0:
        initial_prices = {
            "Carrot": 25.0, "Tomato": 40.0, "Pumpkin": 30.0, "Corn": 20.0,
            "Red_Chili": 80.0, "Bell_Pepper": 90.0, "Cucumber": 25.0, "Unknown": 0.0
        }
        for name, price in initial_prices.items():
            db.add(Product(name=name, price=price))
        db.commit()
        print("✅ Initial Prices Seeded")
    db.close()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()