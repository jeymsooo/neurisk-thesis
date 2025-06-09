"use client";
import React, { useState, useRef } from 'react';
import UserRegistrationForm from '@/components/UserRegistrationForm';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

const defaultUser = {
  name: '',
  age: 25,
  height: 170,
  weight: 70,
  training_frequency: 3,
  previous_injury: 'none',
  muscle_group: 'quadriceps',
  contraction_type: 'isometric',
};

export default function RegisterPage() {
  const [user, setUser] = useState(defaultUser);
  const [duration, setDuration] = useState(5); // default 5 seconds
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [timer, setTimer] = useState<number>(0);
  const [timerActive, setTimerActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [deviceId, setDeviceId] = useState(''); // New state for device ID

  // Start session handler
  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setProcessing(false);
    setLoading(true);
    setSessionId(null);
    setTimer(0);
    try {
      const response = await axios.post(`${API_BASE_URL}/start_session/`, {
        user,
        duration,
        device_id: deviceId,
      });
      setSessionId(response.data.session_id.toString());
      setTimer(duration);
      setTimerActive(true);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to start session');
    } finally {
      setLoading(false);
    }
  };

  // Timer countdown effect
  React.useEffect(() => {
    if (timerActive && timer > 0) {
      timerRef.current = setTimeout(() => setTimer(timer - 1), 1000);
    } else if (timerActive && timer === 0 && sessionId) {
      setTimerActive(false);
      handleEndSession(sessionId);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timerActive, timer, sessionId]);

  // End session and poll for results
  const handleEndSession = async (sessionId: string) => {
    setProcessing(true);
    setError(null);
    try {
      await axios.post(`${API_BASE_URL}/end_session/`, { session_id: sessionId, fs: 1000 });
      pollForResult(sessionId);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to end session');
      setProcessing(false);
    }
  };

  // Poll for session result
  const pollForResult = async (sessionId: string) => {
    let attempts = 0;
    const maxAttempts = 20;
    const poll = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/session_status/`, { params: { session_id: sessionId } });
        if (res.data.status === 'completed' && res.data.result) {
          setResult(res.data.result);
          setProcessing(false);
        } else if (res.data.status === 'failed') {
          setError('Session failed. No EMG data received.');
          setProcessing(false);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1500);
        } else {
          setError('Timed out waiting for result.');
          setProcessing(false);
        }
      } catch (err: any) {
        setError('Error polling for result.');
        setProcessing(false);
      }
    };
    poll();
  };

  // Helper to get initials
  function getInitials(name: string) {
    return name
      .split(' ')
      .map((n) => n[0]?.toUpperCase())
      .join('');
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 bg-white rounded-xl">
      <div className="flex flex-col items-center mb-8">
        <h1 className="text-5xl font-extrabold text-black tracking-tight mb-2">Neurisk</h1>
        <div className="text-sm text-gray-500 font-medium text-center">Muscle Injury Risk Prediction for Basketball Players</div>
      </div>
      <form onSubmit={handleStartSession} className="space-y-6">
        <UserRegistrationForm initialValues={user} onChange={setUser} disabled={loading || timerActive || !!sessionId} />
        <div>
          <label className="block mb-1 font-medium text-black">Device ID (MAC address)</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm placeholder-gray-400 text-black bg-white"
            value={deviceId}
            onChange={e => setDeviceId(e.target.value)}
            placeholder="e.g. 24:6F:28:AA:BB:CC"
            disabled={loading || timerActive || !!sessionId}
            required
          />
        </div>
        <div>
          <label className="block mb-1 font-medium text-black">Session Duration (seconds)</label>
          <input
            type="number"
            className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm placeholder-gray-400 text-black bg-white"
            value={duration}
            onChange={e => setDuration(Number(e.target.value))}
            min={1}
            max={60}
            disabled={loading || timerActive || !!sessionId}
            placeholder="Enter duration"
          />
        </div>
        <button
          type="submit"
          className="bg-black text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-900 shadow"
          disabled={loading || timerActive || !!sessionId || !user.name || !deviceId}
        >
          {loading ? 'Starting...' : 'Start Session'}
        </button>
      </form>
      {sessionId && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
          <div className="mb-2 font-semibold text-black">Session ID: <span className="font-mono">{sessionId}</span></div>
          <div className="mb-2 text-black">Share this Session ID with your ESP32 device to start sending EMG data.</div>
          {timerActive ? (
            <div className="flex items-center gap-2 text-black">
              <svg className="animate-spin h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
              <span>Session in progress... {timer}s left</span>
            </div>
          ) : processing ? (
            <div className="flex items-center gap-2 text-black">
              <svg className="animate-spin h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
              <span>Processing session data...</span>
            </div>
          ) : null}
        </div>
      )}
      {error && <div className="mt-4 text-red-600 bg-red-50 border border-red-200 rounded p-3">{error}</div>}
      {result && (
        <div className="mt-6 p-4 border rounded-xl bg-gray-100 shadow">
          <h2 className="font-semibold mb-2 text-black">Session Result</h2>
          <div className="mb-2 text-black">Risk Score: <span className="font-bold">{result.risk_score}</span></div>
          <div>
            <h3 className="font-semibold text-black">Training Assignment:</h3>
            <pre className="text-xs overflow-x-auto whitespace-pre-wrap bg-white rounded p-2 mt-1 text-black">{result.training_assignment}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
