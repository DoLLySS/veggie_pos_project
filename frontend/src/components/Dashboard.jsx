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