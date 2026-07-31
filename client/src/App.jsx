import { useEffect, useState } from 'react';
import axios from 'axios';
import { NavBar } from './components/NavBar';
import { AuthModal } from './components/AuthModal';
import { ClosetStudio } from './pages/ClosetStudio';
import PrivacyPolicyPage from './PrivacyPolicyPage';

// In production Vercel serves the API from the same origin, so baseURL stays empty.
// Local dev: Vite proxies /api -> FastAPI (see vite.config.js).
axios.defaults.baseURL = import.meta.env.VITE_API_BASE || '';

function App() {
  const [route, setRoute] = useState(
    typeof window !== 'undefined' ? window.location.pathname : '/',
  );
  const [authOpen, setAuthOpen] = useState(false);

  useEffect(() => {
    const onPop = () => setRoute(window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const navigateTo = (path) => {
    window.history.pushState({}, '', path);
    setRoute(path);
  };

  const isPrivacy = route === '/privacy-policy' || route === '/privacy';

  return (
    <div className="min-h-screen bg-ink text-white">
      <NavBar navigateTo={navigateTo} onSignIn={() => setAuthOpen(true)} />

      {isPrivacy ? (
        <div className="mx-auto max-w-3xl px-5 py-16 [&_.text-muted]:text-muted [&_h1]:font-display [&_h1]:text-4xl [&_h2]:mt-8 [&_h2]:font-display [&_h2]:text-xl">
          <PrivacyPolicyPage />
        </div>
      ) : (
        <ClosetStudio />
      )}

      <footer className="border-t border-white/[0.06] py-8 text-center text-xs text-muted">
        <p>StylePilot · AI-powered visual inspiration, never image generation.</p>
        <button onClick={() => navigateTo('/privacy-policy')} className="mt-2 hover:text-white">
          Privacy Policy
        </button>
      </footer>

      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </div>
  );
}

export default App;
