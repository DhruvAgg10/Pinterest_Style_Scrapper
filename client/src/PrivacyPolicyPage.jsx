import { useEffect } from 'react';

function PrivacyPolicyPage() {
  useEffect(() => {
    document.title = 'Privacy Policy | AI Fashion Pose & Style Finder';
  }, []);

  return (
    <div className="card section" style={{ maxWidth: 820, margin: '0 auto' }}>
      <h1 className="heading-lg" style={{ marginBottom: 16 }}>Privacy Policy</h1>
      <p className="text-muted" style={{ marginBottom: 20 }}>
        This Privacy Policy explains how AI Fashion Pose & Style Finder collects, uses, and protects your information.
      </p>

      <div className="grid" style={{ gap: 20 }}>
        <div>
          <h2 className="heading-md" style={{ marginBottom: 8, fontSize: 18 }}>Information We Collect</h2>
          <p className="text-muted">
            We may collect images you upload for analysis, basic account information if you create an account, and technical information such as browser type and IP address.
          </p>
        </div>

        <div>
          <h2 className="heading-md" style={{ marginBottom: 8, fontSize: 18 }}>How We Use Your Information</h2>
          <p className="text-muted">
            Uploaded images are processed to provide fashion analysis, outfit mapping, and inspiration recommendations. We may use anonymized or aggregated data to improve the service.
          </p>
        </div>

        <div>
          <h2 className="heading-md" style={{ marginBottom: 8, fontSize: 18 }}>Sharing of Information</h2>
          <p className="text-muted">
            We do not sell your personal data. We may share information with service providers that help us operate the app, such as hosting, analytics, or model processing providers.
          </p>
        </div>

        <div>
          <h2 className="heading-md" style={{ marginBottom: 8, fontSize: 18 }}>Cookies and Tracking</h2>
          <p className="text-muted">
            The app may use cookies or similar technologies to improve performance and user experience. You can disable cookies in your browser settings if desired.
          </p>
        </div>

        <div>
          <h2 className="heading-md" style={{ marginBottom: 8, fontSize: 18 }}>Security</h2>
          <p className="text-muted">
            We use reasonable technical and organizational measures to protect your data, but no method of transmission over the internet is completely secure.
          </p>
        </div>

        <div>
          <h2 className="heading-md" style={{ marginBottom: 8, fontSize: 18 }}>Your Rights</h2>
          <p className="text-muted">
            Depending on your location, you may have rights to access, delete, or correct your personal information. Please contact us if you would like to exercise those rights.
          </p>
        </div>

        <div>
          <h2 className="heading-md" style={{ marginBottom: 8, fontSize: 18 }}>Contact</h2>
          <p className="text-muted">
            For privacy questions, contact: <strong>support@yourdomain.com</strong>
          </p>
        </div>
      </div>
    </div>
  );
}

export default PrivacyPolicyPage;
