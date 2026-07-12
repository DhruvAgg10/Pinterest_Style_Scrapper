import { useState } from 'react';

const NAV_ITEMS = [
  { path: '/', label: 'Home' },
  { path: '/about', label: 'About' },
  { path: '/company', label: 'Company' },
  { path: '/testing', label: 'Testing' },
  { path: '/fit-check', label: 'Fit Check' },
  { path: '/contact', label: 'Contact' },
];

export function Nav({ navigateTo, active }) {
  const [open, setOpen] = useState(false);

  const go = (path) => {
    setOpen(false);
    navigateTo(path);
  };

  return (
    <div className="nav">
      <div className="nav-inner" style={{ position: 'relative' }}>
        <button className="brand" onClick={() => go('/')}>StylePilot Studio</button>
        <button className="nav-toggle" onClick={() => setOpen((value) => !value)} aria-label="Toggle navigation">
          {open ? '✕' : '☰'}
        </button>
        <div className={`nav-links${open ? ' is-open' : ''}`}>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.path}
              className={`nav-link${active === item.path ? ' is-active' : ''}`}
              onClick={() => go(item.path)}
            >
              {item.label}
            </button>
          ))}
          <button
            className={`nav-link${active === '/privacy-policy' ? ' is-active' : ''}`}
            onClick={() => go('/privacy-policy')}
          >
            Privacy
          </button>
        </div>
      </div>
    </div>
  );
}

export function Footer({ navigateTo }) {
  return (
    <div className="footer">
      <div className="footer-row">
        <a href="mailto:hbuster30@gmail.com" className="btn btn-primary">hbuster30@gmail.com</a>
        <button className="btn btn-secondary" onClick={() => navigateTo('/privacy-policy')}>Privacy policy</button>
        <span className="text-muted" style={{ marginLeft: 'auto', fontSize: 13 }}>© {new Date().getFullYear()} StylePilot Studio</span>
      </div>
    </div>
  );
}

export function Page({ active, navigateTo, children }) {
  return (
    <div className="page">
      <Nav navigateTo={navigateTo} active={active} />
      <div className="container">{children}</div>
    </div>
  );
}
