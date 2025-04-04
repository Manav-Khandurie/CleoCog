'use client';

import { auth, provider } from '@/lib/firebase';
import {
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
} from 'firebase/auth';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      console.log('✅ UID:', result.user.uid);
      router.push('/');
    } catch (err) {
      setError(err.message);
      console.error(err);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      const result = await signInWithPopup(auth, provider);
      console.log('🌐 Google UID:', result.user.uid);
      router.push('/');
    } catch (err) {
      setError(err.message);
      console.error(err);
    }
  };

  return (
    <div style={{ padding: 40, maxWidth: 400, margin: '0 auto' }}>
      <h2>Login</h2>
      <form onSubmit={handleEmailLogin}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ display: 'block', marginBottom: 10 }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ display: 'block', marginBottom: 10 }}
        />
        <button type="submit" style={{ marginBottom: 20 }}>
          Login with Email
        </button>
      </form>
      <button onClick={handleGoogleLogin} style={{ background: '#4285F4', color: '#fff', padding: '8px 16px' }}>
        Login with Google
      </button>

      {error && (
        <p style={{ color: 'red', marginTop: 20 }}>
          {error}
        </p>
      )}
    </div>
  );
}
