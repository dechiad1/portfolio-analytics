import { useState, useCallback, useEffect, type FormEvent } from 'react';
import styles from './AddTickerModal.module.css';

interface AddTickerResponse {
  ticker: string;
  display_name: string;
  asset_type: string;
  exchange: string | null;
  message: string;
}

interface AddTickerModalProps {
  onSubmit: (ticker: string) => Promise<AddTickerResponse>;
  onClose: () => void;
  onSuccess?: () => void;
}

/**
 * AddTickerModal provides a form to add a new ticker for tracking.
 */
export function AddTickerModal({
  onSubmit,
  onClose,
  onSuccess,
}: AddTickerModalProps) {
  const [ticker, setTicker] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<AddTickerResponse | null>(null);

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSubmitting) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose, isSubmitting]);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      setError(null);
      setIsSubmitting(true);

      try {
        const response = await onSubmit(ticker.trim().toUpperCase());
        setSuccessData(response);
        onSuccess?.();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to add ticker';
        setError(message);
      } finally {
        setIsSubmitting(false);
      }
    },
    [ticker, onSubmit, onSuccess]
  );

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !isSubmitting) {
        onClose();
      }
    },
    [onClose, isSubmitting]
  );

  const handleTickerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTicker(e.target.value.toUpperCase());
    setError(null);
  };

  return (
    <div className={styles.overlay} onClick={handleBackdropClick} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Track Ticker</h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {successData ? (
          <div className={styles.successContent}>
            <div className={styles.successIcon}>
              <svg
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
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h3 className={styles.successTitle}>Ticker Added</h3>
            <div className={styles.successDetails}>
              <p><strong>{successData.ticker}</strong> - {successData.display_name}</p>
              <p className={styles.successMeta}>
                {successData.asset_type} {successData.exchange && `on ${successData.exchange}`}
              </p>
            </div>
            <p className={styles.successNote}>
              The ticker will appear with full metrics after the next data refresh.
            </p>
            <button
              type="button"
              className={styles.submitButton}
              onClick={onClose}
            >
              Done
            </button>
          </div>
        ) : (
          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={styles.field}>
              <label htmlFor="ticker" className={styles.label}>
                Ticker Symbol <span className={styles.required}>*</span>
              </label>
              <input
                id="ticker"
                type="text"
                className={styles.input}
                value={ticker}
                onChange={handleTickerChange}
                placeholder="AAPL"
                required
                disabled={isSubmitting}
                autoFocus
                maxLength={20}
              />
              <p className={styles.hint}>
                Enter a stock or ETF ticker symbol (e.g., AAPL, MSFT, SPY)
              </p>
            </div>

            {error && (
              <div className={styles.error}>
                {error}
              </div>
            )}

            <div className={styles.actions}>
              <button
                type="button"
                className={styles.cancelButton}
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className={styles.submitButton}
                disabled={isSubmitting || !ticker.trim()}
              >
                {isSubmitting ? 'Validating...' : 'Add Ticker'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
