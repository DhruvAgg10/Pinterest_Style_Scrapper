import { createClient } from '@supabase/supabase-js';

// Browser-side Supabase client using the public anon key. Safe to expose.
// RLS policies (see supabase/migrations) restrict every user to their own rows.
const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// If env vars are missing (e.g. local dev without keys), export null so the UI
// can degrade gracefully instead of crashing at import time.
export const supabase = url && anonKey ? createClient(url, anonKey) : null;

export const isSupabaseEnabled = Boolean(supabase);
