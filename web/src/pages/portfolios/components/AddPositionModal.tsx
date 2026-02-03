import { useState, useCallback } from 'react';
import type { AddPositionInput } from '../../../shared/types';
import styles from './HoldingModal.module.css';

interface AddPositionModalProps {
  onSubmit: (input: AddPositionInput) => Promise<boolean>;
  onClose: () => void;
  isSubmitting?: boolean;
}

/**
 * AddPositionModal provides a form to add a new position to a portfolio.
 */
export function AddPositionModal({
  onSubmit,
  onClose,
  isSubmitting = false,
}: AddPositionModalProps) {
  const [ticker, setTicker] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [eventDate, setEventDate] = useState(
    new Date().toISOString().split('T')[0]
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      const input: AddPositionInput = {
        ticker: ticker.toUpperCase(),
        quantity: parseFloat(quantity),
        price: parseFloat(price),
        event_date: eventDate,
      };

      const success = await onSubmit(input);
      if (success) {
        onClose();
      }
    },
    [ticker, quantity, price, eventDate, onSubmit, onClose]
  );

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose]
  );

  const isValid =
    ticker.trim() !== '' &&
    parseFloat(quantity) > 0 &&
    parseFloat(price) >= 0 &&
    eventDate !== '';

  return (
    <div className={styles.overlay} onClick={handleOverlayClick} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Add Position</h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
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

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="ticker" className={styles.label}>
              Ticker *
            </label>
            <input
              type="text"
              id="ticker"
              className={styles.input}
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="e.g., AAPL"
              required
              autoFocus
            />
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label htmlFor="quantity" className={styles.label}>
                Quantity *
              </label>
              <input
                type="number"
                id="quantity"
                className={styles.input}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="e.g., 10"
                min="0.0001"
                step="any"
                required
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="price" className={styles.label}>
                Price *
              </label>
              <input
                type="number"
                id="price"
                className={styles.input}
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="e.g., 150.00"
                min="0"
                step="0.01"
                required
              />
            </div>
          </div>

          <div className={styles.field}>
            <label htmlFor="eventDate" className={styles.label}>
              Purchase Date *
            </label>
            <input
              type="date"
              id="eventDate"
              className={styles.input}
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
              required
            />
          </div>

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
              disabled={isSubmitting || !isValid}
            >
              {isSubmitting ? 'Adding...' : 'Add Position'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
