import { useState, useCallback, useEffect, useRef } from 'react';
import type { PortfolioHoldingInput, AssetType } from '../../../shared/types';
import { ASSET_TYPES, ASSET_CLASSES, SECTORS, ASSET_TYPE_TO_API } from '../../../shared/types';
import { searchTickers, getTickerDetails, getTickerPrice, type TickerSearchResult } from '../tickerSearchApi';
import styles from './HoldingModal.module.css';

const BROKERS = ['', 'Fidelity', 'Vanguard', 'Chase', 'Robinhood'] as const;

interface AddHoldingModalProps {
  onSubmit: (input: PortfolioHoldingInput) => Promise<boolean>;
  onClose: () => void;
  isSubmitting: boolean;
}

/**
 * AddHoldingModal provides a form to add a new holding to a portfolio.
 */
export function AddHoldingModal({
  onSubmit,
  onClose,
  isSubmitting,
}: AddHoldingModalProps) {
  const [ticker, setTicker] = useState('');
  const [name, setName] = useState('');
  const [assetType, setAssetType] = useState<string>(ASSET_TYPES[0]);
  const [assetClass, setAssetClass] = useState<string>(ASSET_CLASSES[0]);
  const [sector, setSector] = useState<string>(SECTORS[0]);
  const [broker, setBroker] = useState('');
  const [quantity, setQuantity] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [currentPrice, setCurrentPrice] = useState('');
  const [purchaseDate, setPurchaseDate] = useState('');

  // Ticker search state
  const [searchResults, setSearchResults] = useState<TickerSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

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

  // Debounced ticker search
  useEffect(() => {
    if (ticker.length > 0) {
      setIsSearching(true);

      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }

      debounceTimeout.current = setTimeout(async () => {
        try {
          const results = await searchTickers(ticker, 10);
          setSearchResults(results);
          setShowDropdown(results.length > 0);
        } catch (error) {
          console.error('Failed to search tickers:', error);
          setSearchResults([]);
        } finally {
          setIsSearching(false);
        }
      }, 300);
    } else {
      setSearchResults([]);
      setShowDropdown(false);
      setIsSearching(false);
    }

    return () => {
      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }
    };
  }, [ticker]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectTicker = useCallback(async (result: TickerSearchResult) => {
    setTicker(result.ticker);
    setName(result.name);
    setAssetClass(result.asset_class);
    if (result.category) {
      setSector(result.category);
    }
    setShowDropdown(false);
    setSearchResults([]);

    // Fetch detailed ticker info including prices
    try {
      const details = await getTickerDetails(result.ticker);

      // Auto-populate sector if available
      if (details.sector && (SECTORS as readonly string[]).includes(details.sector)) {
        setSector(details.sector);
      } else if (details.category && (SECTORS as readonly string[]).includes(details.category)) {
        setSector(details.category);
      }

      // Auto-populate prices and date
      if (details.latest_price !== null) {
        setCurrentPrice(details.latest_price.toFixed(2));
        setPurchasePrice(details.latest_price.toFixed(2));
      }
      if (details.latest_price_date) {
        setPurchaseDate(details.latest_price_date);
      }
    } catch (error) {
      console.error('Failed to fetch ticker details:', error);
    }
  }, []);

  // Handler for purchase date changes - fetch historical price
  const handlePurchaseDateChange = useCallback(async (newDate: string) => {
    setPurchaseDate(newDate);

    if (ticker && newDate) {
      try {
        const priceInfo = await getTickerPrice(ticker, newDate);
        setPurchasePrice(priceInfo.price.toFixed(2));
      } catch (error) {
        console.error('Failed to fetch price for date:', error);
        // Keep existing price if fetch fails
      }
    }
  }, [ticker]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const success = await onSubmit({
        ticker: ticker.trim().toUpperCase(),
        name: name.trim(),
        asset_type: ASSET_TYPE_TO_API[assetType as AssetType],
        asset_class: assetClass,
        sector: sector,
        broker: broker.trim() || 'Unknown',
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
          <h2 className={styles.title}>Add Holding</h2>
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
            <div className={`${styles.field} ${styles.tickerField}`} ref={dropdownRef}>
              <label htmlFor="ticker" className={styles.label}>
                Ticker <span className={styles.required}>*</span>
              </label>
              <input
                id="ticker"
                type="text"
                className={styles.input}
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                placeholder="Type to search (e.g., JPM)"
                required
                disabled={isSubmitting}
                autoFocus
                autoComplete="off"
              />
              {isSearching && (
                <span className={styles.searchingIndicator}>Searching...</span>
              )}
              {showDropdown && searchResults.length > 0 && (
                <div className={styles.dropdown}>
                  {searchResults.map((result) => (
                    <div
                      key={result.ticker}
                      className={styles.dropdownItem}
                      onClick={() => handleSelectTicker(result)}
                    >
                      <div className={styles.dropdownTicker}>{result.ticker}</div>
                      <div className={styles.dropdownName}>{result.name}</div>
                      <div className={styles.dropdownAssetClass}>{result.asset_class}</div>
                    </div>
                  ))}
                </div>
              )}
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
                Broker
              </label>
              <select
                id="broker"
                className={styles.select}
                value={broker}
                onChange={(e) => setBroker(e.target.value)}
                disabled={isSubmitting}
              >
                {BROKERS.map((b) => (
                  <option key={b} value={b}>
                    {b || '(Optional)'}
                  </option>
                ))}
              </select>
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
                onChange={(e) => handlePurchaseDateChange(e.target.value)}
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
              {isSubmitting ? 'Adding...' : 'Add Holding'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
