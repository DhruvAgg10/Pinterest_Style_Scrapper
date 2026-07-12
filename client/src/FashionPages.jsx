import { Page, Footer } from './components/Layout';

function SectionCard({ title, body, accent }) {
  return (
    <div className="card card-tight">
      <div className="tile-icon" style={{ background: accent }} />
      <h3 className="heading-md" style={{ marginBottom: 8 }}>{title}</h3>
      <p className="text-muted">{body}</p>
    </div>
  );
}

const UPLOAD_FIELDS = [
  { label: 'Upper wear', name: 'upper_images' },
  { label: 'Lower wear', name: 'lower_images' },
  { label: 'Accessories', name: 'accessories_images' },
  { label: 'Tattoo', name: 'tattoo_images' },
];

export function HomePage({ navigateTo, handleSubmit, upperFiles, setUpperFiles, lowerFiles, setLowerFiles, accessoryFiles, setAccessoryFiles, tattooFiles, setTattooFiles, result, loading, inspiration, captions, captionLoadingKey, handleRecreate }) {
  const fileStates = [upperFiles, lowerFiles, accessoryFiles, tattooFiles];
  const fileSetters = [setUpperFiles, setLowerFiles, setAccessoryFiles, setTattooFiles];

  return (
    <Page active="/" navigateTo={navigateTo}>
      <div className="hero">
        <div>
          <p className="eyebrow" style={{ color: 'rgba(255,255,255,0.75)', marginBottom: 12 }}>AI fashion discovery platform</p>
          <h1 className="heading-xl" style={{ marginBottom: 16 }}>Turn outfit photos into a clear fashion analysis and fit story.</h1>
          <p className="text-muted" style={{ maxWidth: 560, fontSize: 17 }}>StylePilot helps users understand how their upper wear, lower wear, accessories, and tattoos work together, then turns that into styling guidance and visual inspiration.</p>
          <div style={{ marginTop: 24, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button className="btn btn-inverse" onClick={() => navigateTo('/fit-check')}>Explore Fit Check</button>
            <button className="btn btn-ghost-inverse" onClick={() => navigateTo('/about')}>Read About Us</button>
          </div>
        </div>
        <div className="hero-panel">
          <h3>Why it stands out</h3>
          <ul>
            <li>Break down each outfit category for a clearer fashion read</li>
            <li>Surface fit-focused style notes and visual inspiration</li>
            <li>Use AI-assisted interpretation with a polished, user-friendly flow</li>
          </ul>
        </div>
      </div>

      <div className="grid grid-split section">
        <div className="card">
          <h2 className="heading-lg" style={{ marginBottom: 10 }}>Upload your outfit</h2>
          <p className="text-muted" style={{ marginBottom: 20 }}>Add photos for any category you want reviewed — a clearer understanding of fit, mood, and balance follows in seconds.</p>
          <form onSubmit={handleSubmit}>
            <div className="grid" style={{ gap: 12 }}>
              {UPLOAD_FIELDS.map((field, index) => {
                const state = fileStates[index];
                const setter = fileSetters[index];
                const inputId = `upload-${field.name}`;
                return (
                  <div key={field.name} className="upload-field">
                    <label className="field-label" htmlFor={inputId}>{field.label}</label>
                    <input
                      id={inputId}
                      className="upload-input"
                      type="file"
                      multiple
                      onChange={(event) => setter(Array.from(event.target.files || []))}
                    />
                    <label htmlFor={inputId} className="upload-trigger">Choose files</label>
                    <div className="upload-meta">{state.length ? `${state.length} file${state.length > 1 ? 's' : ''} selected` : 'Add one or more images'}</div>
                  </div>
                );
              })}
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary" style={{ marginTop: 20 }}>
              {loading ? 'Analyzing…' : 'Analyze My Look'}
            </button>
          </form>
        </div>

        <div className="card">
          <h3 className="heading-md" style={{ marginBottom: 16 }}>What the experience delivers</h3>
          <div className="grid">
            <SectionCard title="Category mapping" body="Every image is grouped into the right fashion zone so the engine understands the outfit composition clearly." accent="#fef3c7" />
            <SectionCard title="Fit guidance" body="The platform delivers style tags, color cues, and guidance that help users fine-tune silhouette and confidence." accent="#fce7f3" />
            <SectionCard title="Style inspiration" body="Image cards help users explore fashion references that match the mood and structure of the uploaded look." accent="#e0e7ff" />
          </div>
        </div>
      </div>

      <div className="card section">
        <h2 className="heading-lg" style={{ marginBottom: 10 }}>Live analysis preview</h2>
        {result?.error ? <p className="text-muted">{result.error}</p> : (
          <>
            <p className="text-muted" style={{ marginBottom: 20 }}>The engine returns a fashion-focused breakdown of your look, including category mapping, style tags, fit guidance, and inspiration references.</p>
            {result && (
              <div className="grid grid-auto-md" style={{ marginBottom: inspiration?.results?.length ? 24 : 0 }}>
                <div className="card card-tight">
                  <h4 className="heading-md" style={{ marginBottom: 12, fontSize: 16 }}>Recommended tags</h4>
                  <div className="tag-list">
                    {result.recommended_tags?.map((tag) => <span key={tag} className="tag-pill">{tag}</span>)}
                  </div>
                </div>
                <div className="card card-tight">
                  <h4 className="heading-md" style={{ marginBottom: 12, fontSize: 16 }}>Mapped inputs</h4>
                  <div className="grid" style={{ gap: 12 }}>
                    {Object.entries(result.grouped_analysis || {}).map(([key, value]) => (
                      <div key={key}>
                        <strong style={{ textTransform: 'capitalize' }}>{key}</strong>: <span className="text-muted">{value?.style_tags?.join(', ')}</span>
                        {value?.fashion_summary ? <div className="text-muted" style={{ fontSize: 12, marginTop: 4 }}>{value.fashion_summary}</div> : null}
                        {value?.fit_guidance ? <div className="text-muted" style={{ fontSize: 12, marginTop: 2 }}>{value.fit_guidance}</div> : null}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="card card-tight">
                  <h4 className="heading-md" style={{ marginBottom: 12, fontSize: 16 }}>Style story</h4>
                  <p className="text-muted">{result.style_story || 'Your look is being translated into a clear fashion narrative.'}</p>
                </div>
                <div className="card card-tight">
                  <h4 className="heading-md" style={{ marginBottom: 12, fontSize: 16 }}>Fit focus</h4>
                  <p className="text-muted">{result.fit_focus || 'The outfit is reviewed for balance, proportion, and wearable confidence.'}</p>
                </div>
              </div>
            )}
            {inspiration?.results?.length ? (
              <div className="grid grid-auto-sm">
                {inspiration.results.map((item, index) => {
                  const key = `${item.title}-${index}`;
                  const captionResult = captions?.[key];
                  const isLoadingCaption = captionLoadingKey === key;
                  return (
                    <div key={key} className="insp-card">
                      <a href={item.url} target="_blank" rel="noreferrer" className="insp-image-wrap">
                        <img src={item.image_url} alt={item.title} />
                      </a>
                      <div className="insp-body">
                        <div>
                          <div className="insp-title">{item.title}</div>
                          <div className="insp-meta">{item.source}{typeof item.similarity_score === 'number' ? ` · match ${(item.similarity_score * 100).toFixed(0)}%` : ''}</div>
                        </div>
                        <button
                          className="btn btn-secondary btn-sm btn-block"
                          disabled={isLoadingCaption}
                          onClick={() => handleRecreate(item, index)}
                        >
                          {isLoadingCaption ? 'Writing captions…' : 'Recreate & get captions'}
                        </button>
                        {captionResult?.error && <div className="caption-error">{captionResult.error}</div>}
                        {captionResult && !captionResult.error && (
                          <div className="grid" style={{ gap: 6 }}>
                            <div className="caption-block is-normal"><strong>Normal:</strong> {captionResult.normal}</div>
                            <div className="caption-block is-trendy"><strong>Trendy:</strong> {captionResult.trendy}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </>
        )}
      </div>

      <div className="card section">
        <h2 className="heading-lg" style={{ marginBottom: 10 }}>Contact</h2>
        <p className="text-muted" style={{ marginBottom: 16 }}>Need help with a fashion-tech pilot, fit-check concept, or brand styling experience? Reach out and we'll discuss the next steps.</p>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <a href="mailto:hbuster30@gmail.com" className="btn btn-primary">hbuster30@gmail.com</a>
          <button className="btn btn-secondary" onClick={() => navigateTo('/privacy-policy')}>View privacy policy</button>
        </div>
      </div>
    </Page>
  );
}

export function AboutPage({ navigateTo }) {
  return (
    <Page active="/about" navigateTo={navigateTo}>
      <div className="card section" style={{ marginBottom: 24 }}>
        <h1 className="heading-xl" style={{ marginBottom: 16 }}>We make fashion styling feel simple, elegant, and intelligent.</h1>
        <p className="text-muted" style={{ fontSize: 18 }}>StylePilot is a fashion-tech experience built to help users understand how their clothing pieces work together. From outfit mapping to fit review and visual inspiration, the platform turns a messy wardrobe task into an intentional, confident step.</p>
      </div>
      <div className="grid grid-auto-md">
        <SectionCard title="Designed for real dressing" body="We focus on practical outfit logic, not endless scrolling, so the experience feels useful from the first upload." accent="#fde68a" />
        <SectionCard title="Fashion-first, AI-assisted" body="Our engine helps break down an outfit into clear structure while keeping the user experience refined and premium." accent="#fbcfe8" />
        <SectionCard title="Built for brands and creators" body="The product can support brand storytelling, editorial styling, fit check pilots, and personalized recommendations." accent="#c7d2fe" />
      </div>
      <Footer navigateTo={navigateTo} />
    </Page>
  );
}

export function CompanyPage({ navigateTo }) {
  return (
    <Page active="/company" navigateTo={navigateTo}>
      <div className="card section" style={{ marginBottom: 24 }}>
        <h1 className="heading-lg" style={{ marginBottom: 16 }}>A modern fashion technology company creating smarter styling tools.</h1>
        <p className="text-muted" style={{ fontSize: 17 }}>StylePilot Studio is building a premium digital wardrobe assistant for consumers, creators, and fashion brands. The product combines visual analysis, fit guidance, and style storytelling into one polished experience.</p>
      </div>
      <div className="grid grid-auto-md">
        <SectionCard title="Mission" body="Make outfit planning feel clear, expressive, and easy to trust with intelligent but human-friendly design." accent="#e0f2fe" />
        <SectionCard title="Offerings" body="AI-enhanced style analysis, fit check, image mapping, inspiration retrieval, and premium brand-ready tools." accent="#dcfce7" />
      </div>
      <Footer navigateTo={navigateTo} />
    </Page>
  );
}

export function TestingPage({ navigateTo }) {
  return (
    <Page active="/testing" navigateTo={navigateTo}>
      <div className="card section">
        <h1 className="heading-lg" style={{ marginBottom: 16 }}>Every product update is tested for reliability, clarity, and usability.</h1>
        <p className="text-muted">We validate that each upload path works, the analysis returns structured information, the inspiration layer appears correctly, and the experience remains accessible on desktop and mobile.</p>
        <div className="grid grid-auto-md" style={{ marginTop: 20 }}>
          <SectionCard title="Upload testing" body="We confirm image input, category mapping, and response handling for upper, lower, accessory, and tattoo uploads." accent="#fef3c7" />
          <SectionCard title="Analysis testing" body="Each request is checked for structured tags, color cues, and fit-oriented recommendations." accent="#e0e7ff" />
          <SectionCard title="Experience testing" body="The interface is reviewed for clarity, performance, and polished presentation across devices." accent="#fce7f3" />
        </div>
      </div>
      <Footer navigateTo={navigateTo} />
    </Page>
  );
}

export function FitCheckPage({ navigateTo }) {
  return (
    <Page active="/fit-check" navigateTo={navigateTo}>
      <div className="card section">
        <h1 className="heading-lg" style={{ marginBottom: 16 }}>A thoughtful fit check experience for every look.</h1>
        <p className="text-muted">Fit check is about more than size. It is about silhouette, balance, proportion, comfort, and confidence. Our experience helps users review those details in a simple flow.</p>
        <div className="grid grid-auto-md" style={{ marginTop: 20 }}>
          <SectionCard title="Silhouette" body="Review the shape of the outfit and whether it feels balanced from top to bottom." accent="#dcfce7" />
          <SectionCard title="Proportion" body="Check the relationship between layers, accessories, and overall presence." accent="#fef3c7" />
          <SectionCard title="Confidence" body="Highlight the final look as polished, relaxed, or ready for a specific occasion." accent="#fce7f3" />
        </div>
      </div>
      <Footer navigateTo={navigateTo} />
    </Page>
  );
}

export function ContactPage({ navigateTo }) {
  return (
    <Page active="/contact" navigateTo={navigateTo}>
      <div className="card section">
        <h1 className="heading-lg" style={{ marginBottom: 16 }}>Let's build something polished together.</h1>
        <p className="text-muted" style={{ marginBottom: 20 }}>For partnerships, product questions, or collaboration requests, send us a note and we will follow up with the next steps.</p>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <a href="mailto:hbuster30@gmail.com" className="btn btn-primary">hbuster30@gmail.com</a>
          <button className="btn btn-secondary" onClick={() => navigateTo('/privacy-policy')}>Privacy policy</button>
        </div>
      </div>
    </Page>
  );
}
