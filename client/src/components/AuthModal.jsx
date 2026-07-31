import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/Button';

export function AuthModal({ open, onClose }) {
  const { signInWithEmail, signUpWithEmail, enabled } = useAuth();
  const [mode, setMode] = useState('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!enabled) {
      setMessage('Auth is not configured yet.');
      return;
    }
    setBusy(true);
    setMessage(null);
    const fn = mode === 'signin' ? signInWithEmail : signUpWithEmail;
    const { error } = await fn(email, password);
    setBusy(false);
    if (error) return setMessage(error.message);
    if (mode === 'signup') return setMessage('Check your email to confirm, then sign in.');
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.95, y: 10 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: 10 }}
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-sm rounded-2xl glass p-8"
          >
            <button onClick={onClose} className="absolute right-4 top-4 text-muted hover:text-white">
              <X size={18} />
            </button>
            <h2 className="font-display text-2xl text-white">
              {mode === 'signin' ? 'Welcome back' : 'Create account'}
            </h2>
            <p className="mt-1 text-sm text-muted">Save your closet and combos.</p>

            <form onSubmit={submit} className="mt-6 flex flex-col gap-3">
              <input
                type="email"
                required
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 rounded-full bg-white/[0.04] px-5 text-sm outline-none ring-accent/50 focus:ring-2"
              />
              <input
                type="password"
                required
                minLength={6}
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 rounded-full bg-white/[0.04] px-5 text-sm outline-none ring-accent/50 focus:ring-2"
              />
              <Button type="submit" disabled={busy} className="mt-1 w-full">
                {busy ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Sign up'}
              </Button>
            </form>

            {message && <p className="mt-3 text-center text-xs text-accent-soft">{message}</p>}

            <button
              onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
              className="mt-4 w-full text-center text-xs text-muted hover:text-white"
            >
              {mode === 'signin' ? "No account? Sign up" : 'Have an account? Sign in'}
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
