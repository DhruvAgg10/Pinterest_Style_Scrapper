import { useEffect, useState } from 'react';
import axios from 'axios';
import PrivacyPolicyPage from './PrivacyPolicyPage';
import { HomePage, AboutPage, CompanyPage, TestingPage, FitCheckPage, ContactPage } from './FashionPages';
import { Page } from './components/Layout';

// In production (Vercel) VITE_API_BASE points at the Hugging Face Space backend.
// In local dev it stays empty and Vite proxies /api to the local FastAPI server.
axios.defaults.baseURL = import.meta.env.VITE_API_BASE || '';

function App() {
  const [upperFiles, setUpperFiles] = useState([]);
  const [lowerFiles, setLowerFiles] = useState([]);
  const [accessoryFiles, setAccessoryFiles] = useState([]);
  const [tattooFiles, setTattooFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [inspiration, setInspiration] = useState(null);
  const [captions, setCaptions] = useState({});
  const [captionLoadingKey, setCaptionLoadingKey] = useState(null);
  const [currentRoute, setCurrentRoute] = useState(typeof window !== 'undefined' ? window.location.pathname : '/');

  useEffect(() => {
    const handleLocationChange = () => setCurrentRoute(window.location.pathname);
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

  const navigateTo = (path) => {
    window.history.pushState({}, '', path);
    setCurrentRoute(path);
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

  const handleRecreate = async (item, index) => {
    const key = `${item.title}-${index}`;
    setCaptionLoadingKey(key);
    try {
      const response = await axios.post('/api/caption', {
        style_tags: result?.recommended_tags || [],
        title: item.title
      });
      setCaptions((previous) => ({ ...previous, [key]: response.data.captions }));
    } catch (error) {
      console.error(error);
      setCaptions((previous) => ({ ...previous, [key]: { error: 'Could not generate captions. Please try again.' } }));
    } finally {
      setCaptionLoadingKey(null);
    }
  };

  if (currentRoute === '/privacy-policy' || currentRoute === '/privacy') {
    return (
      <Page active="/privacy-policy" navigateTo={navigateTo}>
        <PrivacyPolicyPage />
      </Page>
    );
  }

  if (currentRoute === '/about') {
    return <AboutPage navigateTo={navigateTo} />;
  }

  if (currentRoute === '/company') {
    return <CompanyPage navigateTo={navigateTo} />;
  }

  if (currentRoute === '/testing') {
    return <TestingPage navigateTo={navigateTo} />;
  }

  if (currentRoute === '/fit-check') {
    return <FitCheckPage navigateTo={navigateTo} />;
  }

  if (currentRoute === '/contact') {
    return <ContactPage navigateTo={navigateTo} />;
  }

  return (
    <HomePage
      navigateTo={navigateTo}
      handleSubmit={handleSubmit}
      upperFiles={upperFiles}
      setUpperFiles={setUpperFiles}
      lowerFiles={lowerFiles}
      setLowerFiles={setLowerFiles}
      accessoryFiles={accessoryFiles}
      setAccessoryFiles={setAccessoryFiles}
      tattooFiles={tattooFiles}
      setTattooFiles={setTattooFiles}
      result={result}
      loading={loading}
      inspiration={inspiration}
      captions={captions}
      captionLoadingKey={captionLoadingKey}
      handleRecreate={handleRecreate}
    />
  );
}

export default App;
