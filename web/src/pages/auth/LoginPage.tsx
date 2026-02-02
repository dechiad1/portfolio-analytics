import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../shared/hooks/useAuth';
import { getOAuthLoginUrl } from '../../shared/api/authApi';
import styles from './AuthPage.module.css';

/**
 * LoginPage provides OAuth-based login via Identity Provider.
 */
export function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();

  // Redirect if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/portfolios');
    }
  }, [isAuthenticated, isLoading, navigate]);

  const handleSignIn = () => {
    // Redirect to OAuth provider
    window.location.href = getOAuthLoginUrl();
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.container}>
          <div className={styles.loading}>Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.header}>
          <svg
            className={styles.logo}
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="12" y1="20" x2="12" y2="10" />
            <line x1="18" y1="20" x2="18" y2="4" />
            <line x1="6" y1="20" x2="6" y2="16" />
          </svg>
          <h1 className={styles.title}>Portfolio Analytics</h1>
          <p className={styles.subtitle}>
            Sign in to manage your investment portfolios
          </p>
        </div>

        <div className={styles.oauthSection}>
          <button
            type="button"
            className={styles.submitButton}
            onClick={handleSignIn}
          >
            Sign in with Identity Provider
          </button>
        </div>

        <p className={styles.footer}>
          By signing in, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}
