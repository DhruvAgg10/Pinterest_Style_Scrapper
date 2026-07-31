import { createContext, useContext, useEffect, useState } from 'react';
import { supabase, isSupabaseEnabled } from '../lib/supabase';

const AuthContext = createContext({ user: null, loading: true });

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isSupabaseEnabled) {
      setLoading(false);
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null);
      setLoading(false);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  const signInWithEmail = (email, password) =>
    supabase.auth.signInWithPassword({ email, password });
  const signUpWithEmail = (email, password) =>
    supabase.auth.signUp({
      email,
      password,
      // Send the confirmation link back to the current site, not Supabase's
      // default localhost. The same URL must be allow-listed in Supabase ->
      // Authentication -> URL Configuration (Site URL + Redirect URLs).
      options: { emailRedirectTo: window.location.origin },
    });
  const signOut = () => supabase.auth.signOut();

  return (
    <AuthContext.Provider
      value={{ user, loading, enabled: isSupabaseEnabled, signInWithEmail, signUpWithEmail, signOut }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
