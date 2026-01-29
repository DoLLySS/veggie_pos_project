import os
import textwrap

# --- Veggie POS Pro V3: Dynamic Pricing Edition ---

files = {
    # 1. Docker & Config
    "docker-compose.yml": """
    services:
      db:
        image: postgres:15-alpine
        container_name: veggie_db_pro_v3
        environment:
          - POSTGRES_USER=admin
          - POSTGRES_PASSWORD=securepassword
          - POSTGRES_DB=veggie_db
        volumes:
          - postgres_data:/var/lib/postgresql/data
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U admin -d veggie_db"]
          interval: 5s
          timeout: 5s
          retries: 5

      backend:
        build: ./backend
        container_name: veggie_backend_pro_v3
        ports: ["8000:8000"]
        depends_on:
          db:
            condition: service_healthy
        volumes:
          - ./backend:/app
        command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        privileged: true

      frontend:
        build: ./frontend
        container_name: veggie_frontend_pro_v3
        ports: ["3000:80"]
        depends_on:
          - backend

    volumes:
      postgres_data:
    """,

    # 2. Backend Files
    "backend/Dockerfile": """
    FROM python:3.9-slim
    WORKDIR /app
    RUN apt-get update && apt-get install -y libgl1 libglib2.0-0
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY . .
    """,

    "backend/requirements.txt": """
    fastapi
    uvicorn
    python-multipart
    sqlalchemy
    psycopg2-binary
    passlib==1.7.4
    bcrypt==3.2.0
    python-jose[cryptography]
    scikit-learn
    opencv-python-headless
    numpy
    requests
    pydantic
    """,

    "backend/app/__init__.py": "",

    "backend/app/main.py": """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from .database import init_db
    from .routers import auth, pos, dashboard, products

    app = FastAPI(title="Veggie POS V3")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_db()

    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(pos.router, prefix="/api", tags=["POS"])
    app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
    app.include_router(products.router, prefix="/api", tags=["Products"])

    @app.get("/")
    def root():
        return {"status": "System Online", "version": "3.0.0"}
    """,

    "backend/app/database.py": """
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
    """,

    "backend/app/services/__init__.py": "",

    "backend/app/services/hardware.py": """
    import random
    import time
    import threading

    class HardwareState:
        def __init__(self):
            self.current_weight = 0.0
            self.is_stable = True
            self.tare_offset = 0.0

    state = HardwareState()

    try:
        import RPi.GPIO as GPIO
        from hx711 import HX711
        IS_RASPBERRY_PI = True
        print("✅ Mode: Raspberry Pi (Real Sensor)")
    except ImportError:
        IS_RASPBERRY_PI = False
        print("⚠️ Mode: PC Simulation")

    def scale_reader():
        if IS_RASPBERRY_PI:
            try:
                hx = HX711(dout_pin=5, pd_sck_pin=6)
                hx.set_scale_ratio(1000) 
                hx.reset()
                state.tare_offset = 0
                while True:
                    val = hx.get_weight_mean(5)
                    if val < 0.1: 
                        state.current_weight = 0.0
                        state.is_stable = True
                    else:
                        diff = abs(val - state.current_weight)
                        state.is_stable = diff < 0.1
                        state.current_weight = float(val)
                    time.sleep(0.1)
            except: pass
        else:
            state.tare_offset = 0.5 
            raw = 0.5
            target = 0.5
            while True:
                if random.random() < 0.05: target = random.choice([0.5, 1.5, 3.0, 0.0])
                diff = (target - raw) * 0.1
                raw += diff + random.uniform(-0.02, 0.02)
                state.is_stable = abs(diff) < 0.02
                state.current_weight = max(0, round(raw - state.tare_offset, 2))
                time.sleep(0.1)

    threading.Thread(target=scale_reader, daemon=True).start()

    def get_weight_data():
        return {"weight": state.current_weight, "is_stable": state.is_stable}
    """,

    "backend/app/services/ai_service.py": """
    import random
    CLASSES = ["Carrot", "Tomato", "Pumpkin", "Corn", "Red_Chili", "Bell_Pepper", "Cucumber", "Unknown"]

    def predict_image():
        weights = [1] * (len(CLASSES)-1) + [0.1]
        result = random.choices(CLASSES, weights=weights, k=1)[0]
        return result
    """,

    "backend/app/routers/__init__.py": "",
    "backend/app/routers/auth.py": """
    from fastapi import APIRouter, Depends, HTTPException
    from sqlalchemy.orm import Session
    from pydantic import BaseModel
    from passlib.context import CryptContext
    from jose import jwt
    from datetime import datetime, timedelta
    from ..database import get_db, User

    router = APIRouter()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = "secret"
    ALGORITHM = "HS256"

    class UserAuth(BaseModel):
        username: str
        password: str

    @router.post("/register")
    def register(user: UserAuth, db: Session = Depends(get_db)):
        if db.query(User).filter(User.username == user.username).first():
            return {"msg": "User exists (OK)"} 
        hashed = pwd_context.hash(user.password)
        db.add(User(username=user.username, hashed_password=hashed))
        db.commit()
        return {"msg": "Created"}

    @router.post("/token")
    def login(user: UserAuth, db: Session = Depends(get_db)):
        u = db.query(User).filter(User.username == user.username).first()
        if not u or not pwd_context.verify(user.password, u.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect")
        token = jwt.encode({"sub": u.username, "exp": datetime.utcnow() + timedelta(hours=2)}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    """,

    "backend/app/routers/products.py": """
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
    """,

    "backend/app/routers/pos.py": """
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
    """,

    "backend/app/routers/dashboard.py": """
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
    """,

    "backend/generate_dummy.py": """
    import os, requests
    BASE_DIR = "dataset"
    VEGGIES = ["Carrot", "Tomato", "Pumpkin", "Corn", "Red_Chili", "Bell_Pepper", "Unknown"]
    if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)
    for v in VEGGIES:
        p = os.path.join(BASE_DIR, v)
        os.makedirs(p, exist_ok=True)
        try:
            with open(os.path.join(p, "1.png"), 'wb') as f: f.write(requests.get(f"https://placehold.co/400?text={v}").content)
        except: pass
    print("Done")
    """,

    # 3. Frontend Files
    "frontend/package.json": """
    {
      "name": "veggie-pos-pro",
      "version": "3.0.0",
      "type": "module",
      "scripts": { "dev": "vite", "build": "vite build", "preview": "vite preview" },
      "dependencies": {
        "react": "^18.2.0", "react-dom": "^18.2.0", "axios": "^1.6.0",
        "react-webcam": "^7.2.0", "lucide-react": "^0.292.0", "recharts": "^2.10.0"
      },
      "devDependencies": {
        "@vitejs/plugin-react": "^4.2.0", "autoprefixer": "^10.4.16", "postcss": "^8.4.31", "tailwindcss": "^3.3.5", "vite": "^5.0.0"
      }
    }
    """,

    "frontend/vite.config.js": "import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react'; export default defineConfig({ plugins: [react()], server: { host: true, port: 80 } });",
    "frontend/postcss.config.js": "export default { plugins: { tailwindcss: {}, autoprefixer: {} } }",
    "frontend/tailwind.config.js": "export default { content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'], theme: { extend: {} }, plugins: [] }",
    "frontend/index.html": "<!doctype html><html lang='en'><head><meta charset='UTF-8' /><meta name='viewport' content='width=device-width, initial-scale=1.0' /><title>Veggie POS V3</title></head><body><div id='root'></div><script type='module' src='/src/main.jsx'></script></body></html>",
    "frontend/src/main.jsx": "import React from 'react'; ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>); import ReactDOM from 'react-dom/client'; import App from './App.jsx'; import './index.css';",
    "frontend/src/index.css": "@tailwind base; @tailwind components; @tailwind utilities; body { @apply bg-slate-900 text-white; }",

    "frontend/src/App.jsx": """
    import React, { useState } from 'react';
    import Login from './components/Login';
    import POS from './components/POS';
    import Dashboard from './components/Dashboard';
    import Settings from './components/Settings';

    export default function App() {
      const [token, setToken] = useState(localStorage.getItem('token'));
      const [view, setView] = useState('pos');
      const [username, setUsername] = useState(localStorage.getItem('user') || '');

      if (!token) return <Login setToken={setToken} setUsername={setUsername} />;

      return (
        <div className="h-screen flex flex-col bg-slate-950">
          <div className="bg-slate-900 p-4 border-b border-slate-800 flex justify-between items-center">
            <h1 className="text-xl font-bold text-green-400 flex items-center gap-2">🥬 Veggie POS <span className="text-xs bg-green-900 text-green-300 px-2 py-0.5 rounded">V3</span></h1>
            <div className="flex gap-4">
                <button onClick={()=>setView('pos')} className={`px-4 py-2 rounded ${view==='pos' ? 'bg-green-600' : 'hover:bg-slate-800'}`}>Sell</button>
                <button onClick={()=>setView('dashboard')} className={`px-4 py-2 rounded ${view==='dashboard' ? 'bg-blue-600' : 'hover:bg-slate-800'}`}>Dashboard</button>
                <button onClick={()=>setView('settings')} className={`px-4 py-2 rounded ${view==='settings' ? 'bg-orange-600' : 'hover:bg-slate-800'}`}>Price Settings</button>
                <button onClick={()=>{localStorage.clear(); setToken(null)}} className="px-4 py-2 text-red-400 hover:bg-slate-800">Logout</button>
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            {view === 'pos' && <POS token={token} user={username} />}
            {view === 'dashboard' && <Dashboard token={token} />}
            {view === 'settings' && <Settings token={token} />}
          </div>
        </div>
      );
    }
    """,

    "frontend/src/components/Login.jsx": """
    import React, { useState } from 'react';
    import axios from 'axios';
    export default function Login({ setToken, setUsername }) {
      const [u, setU] = useState(''); const [p, setP] = useState('');
      const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const res = await axios.post('http://localhost:8000/auth/token', { username: u, password: p });
            localStorage.setItem('token', res.data.access_token);
            localStorage.setItem('user', u);
            setToken(res.data.access_token); setUsername(u);
        } catch { alert('Failed'); }
      };
      return (
        <div className="h-screen flex items-center justify-center bg-slate-900">
            <form onSubmit={handleLogin} className="bg-slate-800 p-8 rounded-xl w-96 border border-slate-700">
                <h2 className="text-2xl font-bold text-green-400 mb-6 text-center">Veggie POS Login</h2>
                <input className="w-full p-3 mb-4 rounded bg-slate-700 text-white" placeholder="admin" value={u} onChange={e=>setU(e.target.value)} />
                <input className="w-full p-3 mb-6 rounded bg-slate-700 text-white" type="password" placeholder="1234" value={p} onChange={e=>setP(e.target.value)} />
                <button className="w-full bg-green-600 py-3 rounded font-bold text-white">LOGIN</button>
            </form>
        </div>
      );
    }
    """,

    "frontend/src/components/POS.jsx": """
    import React, { useState, useEffect, useRef } from 'react';
    import Webcam from 'react-webcam';
    import axios from 'axios';
    import { ShoppingCart, Plus, Minus, WifiOff } from 'lucide-react';

    export default function POS({ token, user }) {
      const [data, setData] = useState({ weight: 0, is_stable: true, prices: {} });
      const [cart, setCart] = useState([]);
      const [detected, setDetected] = useState("Scan...");
      const [qty, setQty] = useState(1);
      const [error, setError] = useState(null);
      const webcamRef = useRef(null);

      useEffect(() => {
        const interval = setInterval(async () => {
          try {
            const res = await axios.get('http://localhost:8000/api/status', { headers: { Authorization: `Bearer ${token}` } });
            setData(res.data); setError(null);
            if (webcamRef.current) {
                const img = webcamRef.current.getScreenshot();
                if(img) {
                    const blob = await (await fetch(img)).blob();
                    const fd = new FormData(); fd.append('file', blob, 'img.jpg');
                    const ai = await axios.post('http://localhost:8000/api/predict', fd, { headers: { Authorization: `Bearer ${token}` } });
                    setDetected(ai.data.result);
                }
            }
          } catch { setError("Sensor Disconnected"); }
        }, 1000);
        return () => clearInterval(interval);
      }, []);

      const addToCart = () => {
        if (!data.is_stable) return alert("Unstable Weight");
        const price = data.prices[detected] || 0;
        if (data.weight <= 0) return;
        setCart([...cart, { name: detected, weight: data.weight, price, qty, total: data.weight * price * qty }]);
        setQty(1);
      };

      const checkout = async () => {
        try {
            const total = cart.reduce((a,b)=>a+b.total,0);
            await axios.post('http://localhost:8000/api/checkout', { items: cart, total, cashier: user }, { headers: { Authorization: `Bearer ${token}` } });
            alert("Saved!"); setCart([]);
        } catch { alert("Failed"); }
      };

      return (
        <div className="h-full flex p-4 gap-4">
            {error && <div className="absolute top-20 left-1/2 -translate-x-1/2 bg-red-600 px-6 py-2 rounded-full flex gap-2 items-center shadow-lg z-50 animate-pulse"><WifiOff/> {error}</div>}
            <div className="flex-1 flex flex-col gap-4">
                <div className="flex-1 bg-black rounded-2xl relative overflow-hidden border border-slate-700">
                    <Webcam ref={webcamRef} className="w-full h-full object-cover opacity-80" />
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <span className="bg-black/70 px-4 py-1 rounded text-2xl font-bold">{detected}</span>
                    </div>
                </div>
                <div className="h-48 bg-slate-900 rounded-2xl p-6 flex justify-between items-center border border-slate-800">
                    <div>
                        <div className="text-slate-400">WEIGHT</div>
                        <div className={`text-6xl font-mono font-bold ${data.is_stable ? 'text-blue-400' : 'text-red-500'}`}>{data.weight.toFixed(2)} kg</div>
                        <div className="text-sm text-slate-500 mt-2">Price: {data.prices[detected] || 0} ฿/kg</div>
                    </div>
                    <div className="flex items-center gap-4 bg-slate-800 p-2 rounded-xl">
                        <button onClick={()=>setQty(Math.max(1, qty-1))} className="w-16 h-16 bg-slate-700 rounded-lg text-2xl font-bold"><Minus/></button>
                        <span className="text-4xl font-bold w-12 text-center">{qty}</span>
                        <button onClick={()=>setQty(qty+1)} className="w-16 h-16 bg-slate-700 rounded-lg text-2xl font-bold"><Plus/></button>
                    </div>
                    <button onClick={addToCart} className="bg-green-600 px-8 py-6 rounded-xl text-2xl font-bold shadow-lg">ADD</button>
                </div>
            </div>
            <div className="w-[400px] bg-slate-100 text-slate-900 rounded-2xl p-6 flex flex-col">
                <h2 className="text-2xl font-bold mb-4">Cart</h2>
                <div className="flex-1 overflow-y-auto space-y-2">
                    {cart.map((item, i) => (
                        <div key={i} className="bg-white p-3 rounded-lg shadow-sm flex justify-between">
                            <div><div className="font-bold">{item.name}</div><div className="text-sm">{item.weight}kg x {item.qty}</div></div>
                            <div className="font-bold">{item.total.toFixed(2)}</div>
                        </div>
                    ))}
                </div>
                <div className="mt-4 pt-4 border-t border-slate-300">
                    <div className="flex justify-between text-2xl font-bold mb-4"><span>Total</span><span>{cart.reduce((a,b)=>a+b.total,0).toFixed(2)} ฿</span></div>
                    <button onClick={checkout} disabled={cart.length===0} className="w-full bg-slate-900 text-white py-4 rounded-xl font-bold text-xl">CHECKOUT</button>
                </div>
            </div>
        </div>
      );
    }
    """,

    "frontend/src/components/Dashboard.jsx": """
    import React, { useState, useEffect } from 'react';
    import axios from 'axios';
    export default function Dashboard({ token }) {
      const [stats, setStats] = useState(null);
      useEffect(() => {
        const fetchStats = async () => {
            const res = await axios.get('http://localhost:8000/api/daily', { headers: { Authorization: `Bearer ${token}` } });
            setStats(res.data);
        };
        fetchStats();
      }, []);
      if (!stats) return <div className="p-10 text-white">Loading...</div>;
      return (
        <div className="p-10 text-white h-full overflow-y-auto">
            <h2 className="text-3xl font-bold mb-8">Daily Dashboard</h2>
            <div className="grid grid-cols-2 gap-8 mb-10">
                <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
                    <div className="text-slate-400">Total Sales</div>
                    <div className="text-6xl font-bold text-green-400">{stats.total_sales.toFixed(2)} ฿</div>
                </div>
                <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
                    <div className="text-slate-400">Transactions</div>
                    <div className="text-6xl font-bold text-blue-400">{stats.transaction_count}</div>
                </div>
            </div>
        </div>
      );
    }
    """,

    "frontend/src/components/Settings.jsx": """
    import React, { useState, useEffect } from 'react';
    import axios from 'axios';
    import { Save, Edit2 } from 'lucide-react';

    export default function Settings({ token }) {
      const [products, setProducts] = useState([]);
      const [editing, setEditing] = useState(null);
      const [newPrice, setNewPrice] = useState(0);

      const fetchProducts = async () => {
        const res = await axios.get('http://localhost:8000/api/products', { headers: { Authorization: `Bearer ${token}` } });
        setProducts(res.data.sort((a,b) => a.name.localeCompare(b.name)));
      };

      useEffect(() => { fetchProducts(); }, []);

      const handleEdit = (item) => {
        setEditing(item.id);
        setNewPrice(item.price);
      };

      const handleSave = async (item) => {
        await axios.put(`http://localhost:8000/api/products/${item.name}`, { price: parseFloat(newPrice) }, { headers: { Authorization: `Bearer ${token}` } });
        setEditing(null);
        fetchProducts();
      };

      return (
        <div className="p-10 text-white h-full overflow-y-auto max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold mb-8 text-orange-400">🛠️ Price Settings</h2>
            <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-slate-900 text-slate-400">
                        <tr>
                            <th className="p-4">Vegetable Name</th>
                            <th className="p-4">Current Price (THB/kg)</th>
                            <th className="p-4">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {products.map(p => (
                            <tr key={p.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                                <td className="p-4 font-bold text-lg">{p.name}</td>
                                <td className="p-4">
                                    {editing === p.id ? (
                                        <input type="number" value={newPrice} onChange={e=>setNewPrice(e.target.value)} 
                                        className="bg-slate-900 border border-green-500 rounded p-2 w-32 text-white" autoFocus />
                                    ) : (
                                        <span className="text-green-400 font-mono text-xl">{p.price.toFixed(2)}</span>
                                    )}
                                </td>
                                <td className="p-4">
                                    {editing === p.id ? (
                                        <button onClick={()=>handleSave(p)} className="bg-green-600 hover:bg-green-500 px-4 py-2 rounded flex gap-2 items-center"><Save size={18}/> Save</button>
                                    ) : (
                                        <button onClick={()=>handleEdit(p)} className="bg-slate-600 hover:bg-slate-500 px-4 py-2 rounded flex gap-2 items-center"><Edit2 size={18}/> Edit</button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
      );
    }
    """
}

def create_project():
    print("🚀 Setting up Veggie POS V3 (Dynamic Pricing)...")
    for path, content in files.items():
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name): os.makedirs(dir_name)
        with open(path