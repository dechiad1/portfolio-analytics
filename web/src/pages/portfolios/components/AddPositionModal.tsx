import { useState, useCallback, useEffect, useRef } from 'react';
import type { AddPositionInput } from '../../../shared/types';
import { searchTickers, getTickerDetails, getTickerPrice, type TickerSearchResult } from '../tickerSearchApi';
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
    setShowDropdown(false);
    setSearchResults([]);

    // Fetch detailed ticker info including prices
    try {
      const details = await getTickerDetails(result.ticker);

      // Auto-populate price and date
      if (details.latest_price !== null) {
        setPrice(details.latest_price.toFixed(2));
      }
      if (details.latest_price_date) {
        setEventDate(details.latest_price_date);
      }
    } catch (error) {
      console.error('Failed to fetch ticker details:', error);
    }
  }, []);

  // Handler for purchase date changes - fetch historical price
  const handleDateChange = useCallback(async (newDate: string) => {
    setEventDate(newDate);

    if (ticker && newDate) {
      try {
        const priceInfo = await getTickerPrice(ticker, newDate);
        setPrice(priceInfo.price.toFixed(2));
      } catch (error) {
        console.error('Failed to fetch price for date:', error);
        // Keep existing price if fetch fails
      }
    }
  }, [ticker]);

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
      if (e.target === e.currentTarget && !isSubmitting) {
        onClose();
      }
    },
    [onClose, isSubmitting]
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
            disabled={isSubmitting}
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
          <div className={`${styles.field} ${styles.tickerField}`} ref={dropdownRef}>
            <label htmlFor="ticker" className={styles.label}>
              Ticker <span className={styles.required}>*</span>
            </label>
            <input
              type="text"
              id="ticker"
              className={styles.input}
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="Type to search (e.g., AAPL)"
              required
              autoFocus
              autoComplete="off"
              disabled={isSubmitting}
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

          <div className={styles.row}>
            <div className={styles.field}>
              <label htmlFor="quantity" className={styles.label}>
                Quantity <span className={styles.required}>*</span>
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
                disabled={isSubmitting}
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="price" className={styles.label}>
                Price <span className={styles.required}>*</span>
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
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className={styles.field}>
            <label htmlFor="eventDate" className={styles.label}>
              Purchase Date <span className={styles.required}>*</span>
            </label>
            <input
              type="date"
              id="eventDate"
              className={styles.input}
              value={eventDate}
              onChange={(e) => handleDateChange(e.target.value)}
              required
              disabled={isSubmitting}
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
