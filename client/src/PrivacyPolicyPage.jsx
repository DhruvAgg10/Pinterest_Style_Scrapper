import { useEffect } from 'react';

function PrivacyPolicyPage() {
  useEffect(() => {
    document.title = 'Privacy Policy | AI Fashion Pose & Style Finder';
  }, []);

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 900, margin: '0 auto', padding: 24, lineHeight: 1.6 }}>
      <h1>Privacy Policy</h1>
      <p>
        This Privacy Policy explains how AI Fashion Pose & Style Finder collects, uses, and protects your information.
      </p>

      <h2>Information We Collect</h2>
      <p>
        We may collect images you upload for analysis, basic account information if you create an account, and technical information such as browser type and IP address.
      </p>

      <h2>How We Use Your Information</h2>
      <p>
        Uploaded images are processed to provide fashion analysis, outfit mapping, and inspiration recommendations. We may use anonymized or aggregated data to improve the service.
      </p>

      <h2>Sharing of Information</h2>
      <p>
        We do not sell your personal data. We may share information with service providers that help us operate the app, such as hosting, analytics, or model processing providers.
      </p>

      <h2>Cookies and Tracking</h2>
      <p>
        The app may use cookies or similar technologies to improve performance and user experience. You can disable cookies in your browser settings if desired.
      </p>

      <h2>Security</h2>
      <p>
        We use reasonable technical and organizational measures to protect your data, but no method of transmission over the internet is completely secure.
      </p>

      <h2>Your Rights</h2>
      <p>
        Depending on your location, you may have rights to access, delete, or correct your personal information. Please contact us if you would like to exercise those rights.
      </p>

      <h2>Contact</h2>
      <p>
        For privacy questions, contact: <strong>support@yourdomain.com</strong>
      </p>
    </div>
  );
}

export default PrivacyPolicyPage;
