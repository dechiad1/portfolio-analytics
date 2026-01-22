import { useState, useCallback, useEffect, type FormEvent } from 'react';
import type { PortfolioHolding, PortfolioHoldingInput, AssetType } from '../../../shared/types';
import { ASSET_TYPES, ASSET_CLASSES, SECTORS, ASSET_TYPE_TO_API, API_TO_ASSET_TYPE } from '../../../shared/types';
import styles from './HoldingModal.module.css';

interface EditHoldingModalProps {
  holding: PortfolioHolding;
  onSubmit: (input: PortfolioHoldingInput) => Promise<boolean>;
  onClose: () => void;
  isSubmitting: boolean;
}

/**
 * EditHoldingModal provides a form to edit an existing holding.
 */
export function EditHoldingModal({
  holding,
  onSubmit,
  onClose,
  isSubmitting,
}: EditHoldingModalProps) {
  const [ticker, setTicker] = useState(holding.ticker);
  const [name, setName] = useState(holding.name);
  const [assetType, setAssetType] = useState(API_TO_ASSET_TYPE[holding.asset_type] || holding.asset_type);
  const [assetClass, setAssetClass] = useState(holding.asset_class);
  const [sector, setSector] = useState(holding.sector);
  const [broker, setBroker] = useState(holding.broker);
  const [quantity, setQuantity] = useState(holding.quantity.toString());
  const [purchasePrice, setPurchasePrice] = useState(holding.purchase_price.toString());
  const [currentPrice, setCurrentPrice] = useState(holding.current_price.toString());
  const [purchaseDate, setPurchaseDate] = useState(holding.purchase_date.split('T')[0]);

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
      const success = await onSubmit({
        ticker: ticker.trim().toUpperCase(),
        name: name.trim(),
        asset_type: ASSET_TYPE_TO_API[assetType as AssetType] || assetType,
        asset_class: assetClass,
        sector: sector,
        broker: broker.trim(),
        quantity: parseFloat(quantity),
        purchase_price: parseFloat(purchasePrice),
        current_price: parseFloat(currentPrice),
        purchase_date: purchaseDate,
      });
      if (success) {
        onClose();
      }
    },
    [
      ticker,
      name,
      assetType,
      assetClass,
      sector,
      broker,
      quantity,
      purchasePrice,
      currentPrice,
      purchaseDate,
      onSubmit,
      onClose,
    ]
  );

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !isSubmitting) {
        onClose();
      }
    },
    [onClose, isSubmitting]
  );

  return (
    <div className={styles.overlay} onClick={handleBackdropClick} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Edit Holding</h2>
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
          <div className={styles.row}>
            <div className={styles.field}>
              <label htmlFor="ticker" className={styles.label}>
                Ticker <span className={styles.required}>*</span>
              </label>
              <input
                id="ticker"
                type="text"
                className={styles.input}
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                placeholder="AAPL"
                required
                disabled={isSubmitting}
              />
            </div>
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
                placeholder="Apple Inc."
                required
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label htmlFor="assetType" className={styles.label}>
                Asset Type <span className={styles.required}>*</span>
              </label>
              <select
                id="assetType"
                className={styles.select}
                value={assetType}
                onChange={(e) => setAssetType(e.target.value)}
                required
                disabled={isSubmitting}
              >
                {ASSET_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
            <div className={styles.field}>
              <label htmlFor="assetClass" className={styles.label}>
                Asset Class <span className={styles.required}>*</span>
              </label>
              <select
                id="assetClass"
                className={styles.select}
                value={assetClass}
                onChange={(e) => setAssetClass(e.target.value)}
                required
                disabled={isSubmitting}
              >
                {ASSET_CLASSES.map((cls) => (
                  <option key={cls} value={cls}>
                    {cls}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label htmlFor="sector" className={styles.label}>
                Sector <span className={styles.required}>*</span>
              </label>
              <select
                id="sector"
                className={styles.select}
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                required
                disabled={isSubmitting}
              >
                {SECTORS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className={styles.field}>
              <label htmlFor="broker" className={styles.label}>
                Broker <span className={styles.required}>*</span>
              </label>
              <input
                id="broker"
                type="text"
                className={styles.input}
                value={broker}
                onChange={(e) => setBroker(e.target.value)}
                placeholder="Fidelity"
                required
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label htmlFor="quantity" className={styles.label}>
                Quantity <span className={styles.required}>*</span>
              </label>
              <input
                id="quantity"
                type="number"
                className={styles.input}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="100"
                required
                min="0"
                step="any"
                disabled={isSubmitting}
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="purchaseDate" className={styles.label}>
                Purchase Date <span className={styles.required}>*</span>
              </label>
              <input
                id="purchaseDate"
                type="date"
                className={styles.input}
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
                required
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label htmlFor="purchasePrice" className={styles.label}>
                Purchase Price ($) <span className={styles.required}>*</span>
              </label>
              <input
                id="purchasePrice"
                type="number"
                className={styles.input}
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(e.target.value)}
                placeholder="150.00"
                required
                min="0"
                step="0.01"
                disabled={isSubmitting}
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="currentPrice" className={styles.label}>
                Current Price ($) <span className={styles.required}>*</span>
              </label>
              <input
                id="currentPrice"
                type="number"
                className={styles.input}
                value={currentPrice}
                onChange={(e) => setCurrentPrice(e.target.value)}
                placeholder="175.00"
                required
                min="0"
                step="0.01"
                disabled={isSubmitting}
              />
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
