// [NEW] Settings Component for Price Editing
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