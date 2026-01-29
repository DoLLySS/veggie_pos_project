import React, { useState } from 'react';
import Login from './components/Login';
import POS from './components/POS';
import Dashboard from './components/Dashboard';
import Settings from './components/Settings'; // New Component

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