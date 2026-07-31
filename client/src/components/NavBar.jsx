import { Sparkles, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/Button';

export function NavBar({ navigateTo, onSignIn }) {
  const { user, signOut, enabled } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-ink/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <button onClick={() => navigateTo('/')} className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-ink">
            <Sparkles size={16} />
          </span>
          <span className="font-display text-lg tracking-wide">StylePilot</span>
        </button>

        <div className="flex items-center gap-3">
          {enabled && user ? (
            <>
              <span className="hidden text-sm text-muted sm:inline">{user.email}</span>
              <Button variant="ghost" size="sm" onClick={signOut}>
                <LogOut size={14} />
                Sign out
              </Button>
            </>
          ) : (
            <Button variant="ghost" size="sm" onClick={onSignIn}>
              Sign in
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
