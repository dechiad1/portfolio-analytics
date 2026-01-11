import { useState, useEffect } from 'react';
import type { Holding, HoldingInput } from '../../../shared/types';
import { ASSET_CLASSES, SECTORS } from '../../../shared/types';
import styles from './EditHoldingModal.module.css';

interface EditHoldingModalProps {
  /** The holding to edit */
  holding: Holding;
  /** Callback when form is submitted */
  onSubmit: (holdingId: string, data: HoldingInput) => Promise<boolean>;
  /** Callback when modal is closed */
  onClose: () => void;
  /** Whether submission is in progress */
  isSubmitting?: boolean;
}

/**
 * EditHoldingModal provides a modal form for editing existing holdings.
 */
export function EditHoldingModal({
  holding,
  onSubmit,
  onClose,
  isSubmitting = false,
}: EditHoldingModalProps) {
  const [formData, setFormData] = useState<HoldingInput>({
    ticker: holding.ticker,
    name: holding.name,
    asset_class: holding.asset_class,
    sector: holding.sector,
    broker: holding.broker,
    purchase_date: holding.purchase_date.split('T')[0],
  });
  const [errors, setErrors] = useState<Partial<Record<keyof HoldingInput, string>>>({});

  // Update form when holding changes
  useEffect(() => {
    setFormData({
      ticker: holding.ticker,
      name: holding.name,
      asset_class: holding.asset_class,
      sector: holding.sector,
      broker: holding.broker,
      purchase_date: holding.purchase_date.split('T')[0],
    });
  }, [holding]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSubmitting) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose, isSubmitting]);

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof HoldingInput, string>> = {};

    if (!formData.ticker.trim()) {
      newErrors.ticker = 'Ticker is required';
    } else if (formData.ticker.length > 10) {
      newErrors.ticker = 'Ticker must be 10 characters or less';
    }

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.asset_class) {
      newErrors.asset_class = 'Asset class is required';
    }

    if (!formData.sector) {
      newErrors.sector = 'Sector is required';
    }

    if (!formData.broker.trim()) {
      newErrors.broker = 'Broker is required';
    }

    if (!formData.purchase_date) {
      newErrors.purchase_date = 'Purchase date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof HoldingInput]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    const success = await onSubmit(holding.id, {
      ...formData,
      ticker: formData.ticker.toUpperCase().trim(),
      name: formData.name.trim(),
      broker: formData.broker.trim(),
    });

    if (success) {
      onClose();
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isSubmitting) {
      onClose();
    }
  };

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.modal} role="dialog" aria-labelledby="edit-modal-title">
        <div className={styles.header}>
          <h2 id="edit-modal-title" className={styles.title}>
            Edit Holding
          </h2>
          <button
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

        <form onSubmit={handleSubmit}>
          <div className={styles.formGrid}>
            <div className={styles.field}>
              <label htmlFor="edit-ticker" className={styles.label}>
                Ticker Symbol
              </label>
              <input
                type="text"
                id="edit-ticker"
                name="ticker"
                value={formData.ticker}
                onChange={handleChange}
                className={`${styles.input} ${errors.ticker ? styles.inputError : ''}`}
                disabled={isSubmitting}
              />
              {errors.ticker && <span className={styles.error}>{errors.ticker}</span>}
            </div>

            <div className={styles.field}>
              <label htmlFor="edit-name" className={styles.label}>
                Name
              </label>
              <input
                type="text"
                id="edit-name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`${styles.input} ${errors.name ? styles.inputError : ''}`}
                disabled={isSubmitting}
              />
              {errors.name && <span className={styles.error}>{errors.name}</span>}
            </div>

            <div className={styles.field}>
              <label htmlFor="edit-asset_class" className={styles.label}>
                Asset Class
              </label>
              <select
                id="edit-asset_class"
                name="asset_class"
                value={formData.asset_class}
                onChange={handleChange}
                className={`${styles.select} ${errors.asset_class ? styles.inputError : ''}`}
                disabled={isSubmitting}
              >
                <option value="">Select asset class</option>
                {ASSET_CLASSES.map((ac) => (
                  <option key={ac} value={ac}>
                    {ac}
                  </option>
                ))}
              </select>
              {errors.asset_class && (
                <span className={styles.error}>{errors.asset_class}</span>
              )}
            </div>

            <div className={styles.field}>
              <label htmlFor="edit-sector" className={styles.label}>
                Sector
              </label>
              <select
                id="edit-sector"
                name="sector"
                value={formData.sector}
                onChange={handleChange}
                className={`${styles.select} ${errors.sector ? styles.inputError : ''}`}
                disabled={isSubmitting}
              >
                <option value="">Select sector</option>
                {SECTORS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              {errors.sector && <span className={styles.error}>{errors.sector}</span>}
            </div>

            <div className={styles.field}>
              <label htmlFor="edit-broker" className={styles.label}>
                Broker
              </label>
              <input
                type="text"
                id="edit-broker"
                name="broker"
                value={formData.broker}
                onChange={handleChange}
                className={`${styles.input} ${errors.broker ? styles.inputError : ''}`}
                disabled={isSubmitting}
              />
              {errors.broker && <span className={styles.error}>{errors.broker}</span>}
            </div>

            <div className={styles.field}>
              <label htmlFor="edit-purchase_date" className={styles.label}>
                Purchase Date
              </label>
              <input
                type="date"
                id="edit-purchase_date"
                name="purchase_date"
                value={formData.purchase_date}
                onChange={handleChange}
                className={`${styles.input} ${errors.purchase_date ? styles.inputError : ''}`}
                disabled={isSubmitting}
              />
              {errors.purchase_date && (
                <span className={styles.error}>{errors.purchase_date}</span>
              )}
            </div>
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
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
