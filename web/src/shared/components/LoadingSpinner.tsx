import styles from './LoadingSpinner.module.css';

interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: 'small' | 'medium' | 'large';
  /** Optional message to display below the spinner */
  message?: string;
}

/**
 * LoadingSpinner component displays a spinning animation
 * to indicate loading state.
 */
export function LoadingSpinner({
  size = 'medium',
  message,
}: LoadingSpinnerProps) {
  return (
    <div className={styles.container}>
      <div className={`${styles.spinner} ${styles[size]}`} role="status">
        <span className={styles.srOnly}>Loading...</span>
      </div>
      {message && <p className={styles.message}>{message}</p>}
    </div>
  );
}
