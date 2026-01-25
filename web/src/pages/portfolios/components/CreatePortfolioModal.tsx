import { useState, useCallback, useEffect, type FormEvent } from 'react';
import type { PortfolioInput, CreationMode, CreatePortfolioResult } from '../../../shared/types';
import { CreationModeSelector } from './CreationModeSelector';
import { DictationInput } from './DictationInput';
import styles from './CreatePortfolioModal.module.css';

interface CreatePortfolioModalProps {
  onSubmit: (input: PortfolioInput) => Promise<CreatePortfolioResult | null>;
  onClose: () => void;
  isSubmitting: boolean;
}

const CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF'] as const;
const DEFAULT_TOTAL_VALUE = 100000;

/**
 * CreatePortfolioModal provides a form to create a new portfolio.
 */
export function CreatePortfolioModal({
  onSubmit,
  onClose,
  isSubmitting,
}: CreatePortfolioModalProps) {
  const [name, setName] = useState('');
  const [baseCurrency, setBaseCurrency] = useState('USD');
  const [creationMode, setCreationMode] = useState<CreationMode>('empty');
  const [totalValue, setTotalValue] = useState(DEFAULT_TOTAL_VALUE);
  const [description, setDescription] = useState('');
  const [result, setResult] = useState<CreatePortfolioResult | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);

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
      const input: PortfolioInput = {
        name: name.trim(),
        base_currency: baseCurrency,
        creation_mode: creationMode,
      };

      if (creationMode === 'random' || creationMode === 'dictation') {
        input.total_value = totalValue;
      }

      if (creationMode === 'dictation') {
        input.description = description.trim();
      }

      const portfolioResult = await onSubmit(input);

      if (portfolioResult) {
        setResult(portfolioResult);
        if (portfolioResult.unmatched_descriptions.length > 0) {
          setShowTooltip(true);
          // Auto-close after showing the tooltip
          setTimeout(() => {
            onClose();
          }, 3000);
        } else {
          onClose();
        }
      }
    },
    [name, baseCurrency, creationMode, totalValue, description, onSubmit, onClose]
  );

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !isSubmitting) {
        onClose();
      }
    },
    [onClose, isSubmitting]
  );

  const isFormValid = () => {
    if (!name.trim()) return false;
    if (creationMode === 'dictation' && !description.trim()) return false;
    return true;
  };

  return (
    <div className={styles.overlay} onClick={handleBackdropClick} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Create Portfolio</h2>
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

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label htmlFor="name" className={styles.label}>
              Name <span className={styles.required}>*</span>
            </label>
            <input
              id="name"
              type="text"
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Portfolio"
              required
              disabled={isSubmitting}
              autoFocus
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="baseCurrency" className={styles.label}>
              Base Currency
            </label>
            <select
              id="baseCurrency"
              className={styles.select}
              value={baseCurrency}
              onChange={(e) => setBaseCurrency(e.target.value)}
              disabled={isSubmitting}
            >
              {CURRENCIES.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>
          </div>

          <CreationModeSelector
            value={creationMode}
            onChange={setCreationMode}
            disabled={isSubmitting}
          />

          {(creationMode === 'random' || creationMode === 'dictation') && (
            <div className={styles.field}>
              <label htmlFor="totalValue" className={styles.label}>
                Total Portfolio Value ({baseCurrency})
              </label>
              <input
                id="totalValue"
                type="number"
                className={styles.input}
                value={totalValue}
                onChange={(e) => setTotalValue(Number(e.target.value))}
                min={1000}
                step={1000}
                disabled={isSubmitting}
              />
            </div>
          )}

          {creationMode === 'dictation' && (
            <DictationInput
              value={description}
              onChange={setDescription}
              disabled={isSubmitting}
            />
          )}

          {showTooltip && result && result.unmatched_descriptions.length > 0 && (
            <div className={styles.tooltip}>
              <p className={styles.tooltipTitle}>
                Portfolio created with {result.holdings_created} holdings
              </p>
              <p className={styles.tooltipNote}>Some items could not be matched:</p>
              <ul className={styles.tooltipList}>
                {result.unmatched_descriptions.map((desc, i) => (
                  <li key={i}>{desc}</li>
                ))}
              </ul>
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
              disabled={isSubmitting || !isFormValid()}
            >
              {isSubmitting ? 'Creating...' : 'Create Portfolio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
