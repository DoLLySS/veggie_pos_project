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