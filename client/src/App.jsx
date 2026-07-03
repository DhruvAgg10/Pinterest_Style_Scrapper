import { useState } from 'react';
import axios from 'axios';

function App() {
  const [outfitFiles, setOutfitFiles] = useState([]);
  const [tattooFiles, setTattooFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    const formData = new FormData();

    outfitFiles.forEach((file) => formData.append('outfit_images', file));
    tattooFiles.forEach((file) => formData.append('tattoo_images', file));

    try {
      const response = await axios.post('/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (error) {
      console.error(error);
      setResult({ error: 'Analysis failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 900, margin: '0 auto', padding: 24 }}>
      <h1>AI Fashion Pose & Style Finder</h1>
      <p>Upload outfit and tattoo images to receive style-based inspiration recommendations.</p>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 16 }}>
          <label><strong>Outfit images</strong></label>
          <input type="file" multiple onChange={(event) => setOutfitFiles(Array.from(event.target.files || []))} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label><strong>Tattoo images</strong></label>
          <input type="file" multiple onChange={(event) => setTattooFiles(Array.from(event.target.files || []))} />
        </div>

        <button type="submit" disabled={loading}>{loading ? 'Analyzing…' : 'Analyze Images'}</button>
      </form>

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
              <h2>Results</h2>
              <ul>
                {result.results?.map((item, index) => (
                  <li key={`${item.title}-${index}`}>
                    <strong>{item.title}</strong> — {item.source} (score {item.score})
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
