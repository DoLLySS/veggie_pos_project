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