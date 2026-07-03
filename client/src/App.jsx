import { useEffect, useState } from 'react';
import axios from 'axios';
import PrivacyPolicyPage from './PrivacyPolicyPage';

function App() {
  const [upperFiles, setUpperFiles] = useState([]);
  const [lowerFiles, setLowerFiles] = useState([]);
  const [accessoryFiles, setAccessoryFiles] = useState([]);
  const [tattooFiles, setTattooFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [inspiration, setInspiration] = useState(null);
  const [currentRoute, setCurrentRoute] = useState(typeof window !== 'undefined' ? window.location.pathname : '/');
  const [privacyUrl, setPrivacyUrl] = useState(typeof window !== 'undefined' ? `${window.location.origin}/privacy-policy` : 'https://ai-fashion-pose-style-finder.vercel.app/privacy-policy');

  useEffect(() => {
    const handleLocationChange = () => setCurrentRoute(window.location.pathname);
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

  const navigateTo = (path) => {
    window.history.pushState({}, '', path);
    setCurrentRoute(path);
    if (path === '/privacy-policy') {
      setPrivacyUrl(`${window.location.origin}/privacy-policy`);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    const formData = new FormData();

    upperFiles.forEach((file) => formData.append('upper_images', file));
    lowerFiles.forEach((file) => formData.append('lower_images', file));
    accessoryFiles.forEach((file) => formData.append('accessories_images', file));
    tattooFiles.forEach((file) => formData.append('tattoo_images', file));

    try {
      const response = await axios.post('/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
      setInspiration(response.data.inspiration || null);
    } catch (error) {
      console.error(error);
      setResult({ error: 'Analysis failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  if (currentRoute === '/privacy-policy' || currentRoute === '/privacy') {
    return (
      <div>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '12px 24px 0' }}>
          <button onClick={() => navigateTo('/')} style={{ cursor: 'pointer' }}>Back to app</button>
        </div>
        <PrivacyPolicyPage />
      </div>
    );
  }

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 900, margin: '0 auto', padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>AI Fashion Pose & Style Finder</h1>
        <button onClick={() => navigateTo('/privacy-policy')} style={{ cursor: 'pointer' }}>Privacy Policy</button>
      </div>
      <p>Upload separate images for upper wear, lower wear, accessories, and tattoos. The engine now runs a live image-analysis pipeline and returns structured results for each category.</p>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 16 }}>
          <label><strong>Upper wear</strong></label>
          <input type="file" multiple onChange={(event) => setUpperFiles(Array.from(event.target.files || []))} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label><strong>Lower wear</strong></label>
          <input type="file" multiple onChange={(event) => setLowerFiles(Array.from(event.target.files || []))} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label><strong>Accessories</strong></label>
          <input type="file" multiple onChange={(event) => setAccessoryFiles(Array.from(event.target.files || []))} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label><strong>Tattoo</strong></label>
          <input type="file" multiple onChange={(event) => setTattooFiles(Array.from(event.target.files || []))} />
        </div>

        <button type="submit" disabled={loading}>{loading ? 'Analyzing…' : 'Analyze Images'}</button>
      </form>

      <p style={{ marginTop: 12 }}>
        For Pinterest API access, use this privacy policy page URL in your app submission and documentation: <strong>{privacyUrl}</strong>
      </p>

      {result && (
        <div style={{ marginTop: 24 }}>
          {result.error ? (
            <p>{result.error}</p>
          ) : (
            <>
              <h2>Recommended tags</h2>
              <ul>
                {result.recommended_tags?.map((tag) => <li key={tag}>{tag}</li>)}
              </ul>
              <h2>Mapped inputs</h2>
              <ul>
                {Object.entries(result.grouped_analysis || {}).map(([key, value]) => (
                  <li key={key}>
                    <strong>{key}</strong>: {value?.style_tags?.join(', ')}
                    {value?.analysis_mode ? ` · ${value.analysis_mode}` : ''}
                  </li>
                ))}
              </ul>
              <h2>Results</h2>
              <ul>
                {result.results?.map((item, index) => (
                  <li key={`${item.title}-${index}`}>
                    <strong>{item.title}</strong> — {item.source} (score {item.score})
                  </li>
                ))}
              </ul>
              <h2>Live inspiration</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
                {inspiration?.results?.map((item, index) => (
                  <div key={`${item.title}-${index}`} style={{ border: '1px solid #ddd', borderRadius: 8, padding: 8 }}>
                    <a href={item.url} target="_blank" rel="noreferrer">
                      <img src={item.image_url} alt={item.title} style={{ width: '100%', height: 160, objectFit: 'cover', borderRadius: 6 }} />
                    </a>
                    <div style={{ marginTop: 8 }}>
                      <strong>{item.title}</strong>
                      <div style={{ color: '#666', fontSize: 12 }}>{item.source}</div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
