// eslint-disable-next-line @typescript-eslint/no-unused-vars
"use client";
import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

function getInitials(name: string) {
  return name
    .split(' ')
    .map((n) => n[0]?.toUpperCase())
    .join('');
}

function riskColor(risk: string) {
  return 'text-black bg-gray-100 border border-gray-300';
}

function TrainingRegime({ risk, assignment }: { risk: string; assignment: string }) {
  return (
    <div className="mt-4 p-4 rounded-xl border bg-gray-50">
      <h3 className="font-bold text-lg mb-2">Training Regime ({risk.charAt(0).toUpperCase() + risk.slice(1)})</h3>
      <pre className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-100 rounded p-3">{assignment}</pre>
    </div>
  );
}

type SearchResult = {
  user: { id: string; name: string };
  risk_score?: string;
  timestamp: string;
  training_assignment: string;
};

export default function SearchPage() {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const url = name
        ? `${API_BASE_URL}/user_risk_scores/?name=${encodeURIComponent(name)}`
        : `${API_BASE_URL}/user_risk_scores/`;
      const response = await axios.get(url);
      setResults(response.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || 'Search failed');
      } else {
        setError('Search failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-10 px-4">
      <h1 className="text-3xl font-extrabold mb-2 text-center text-black">User Results</h1>
      <p className="text-center text-gray-500 mb-8">Search for previous users and view their risk scores and training regimes.</p>
      <form onSubmit={handleSearch} className="flex gap-2 mb-8 justify-center">
        <input
          type="text"
          className="flex-1 max-w-xs border border-gray-300 rounded-lg px-4 py-2 shadow-sm placeholder-gray-400 text-black bg-white"
          placeholder="Search by name (optional)"
          value={name}
          onChange={e => setName(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="bg-black text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-900 disabled:opacity-50 shadow"
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      {error && <div className="mb-4 text-red-600 bg-red-50 border border-red-200 rounded p-3 text-center">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {results.length === 0 && !loading && <div className="text-gray-400 col-span-2 text-center">No results.</div>}
        {results.map((item, idx) => {
          const initials = getInitials(item.user.name);
          return (
            <div
              key={item.user.id || idx}
              className="relative bg-white rounded-2xl shadow-md p-6 flex flex-col gap-2 border hover:shadow-lg transition cursor-pointer"
              onClick={() => setExpanded(expanded === idx ? null : idx)}
            >
              <div className="flex items-center gap-4">
                <div className={`w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold bg-white border border-gray-300 text-black`}>{initials}</div>
                <div className="flex-1">
                  <div className="font-bold text-lg text-black">{item.user.name}</div>
                  <div className="text-xs text-gray-500">{new Date(item.timestamp).toLocaleString()}</div>
                </div>
                <div className={`text-xl font-bold px-4 py-1 rounded-full ${riskColor(item.risk_score?.toLowerCase() || 'unknown')}`}>{item.risk_score}</div>
              </div>
              {expanded === idx && (
                <TrainingRegime risk={item.risk_score?.toLowerCase() || 'unknown'} assignment={item.training_assignment} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
