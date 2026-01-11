import { useState, useEffect, useRef } from 'react';
import type { HoldingInput } from '../../../shared/types';
import { ASSET_CLASSES, SECTORS } from '../../../shared/types';
import { searchTickers, type TickerSearchResult } from '../tickerSearchApi';
import styles from './AddHoldingForm.module.css';

interface AddHoldingFormProps {
  /** Callback when form is submitted */
  onSubmit: (holding: HoldingInput) => Promise<boolean>;
  /** Callback when form is cancelled */
  onCancel: () => void;
  /** Whether submission is in progress */
  isSubmitting?: boolean;
}

/**
 * Get today's date in YYYY-MM-DD format.
 */
function getTodayDate(): string {
  return new Date().toISOString().split('T')[0];
}

/**
 * AddHoldingForm provides a form for adding new holdings.
 */
export function AddHoldingForm({
  onSubmit,
  onCancel,
  isSubmitting = false,
}: AddHoldingFormProps) {
  const [formData, setFormData] = useState<HoldingInput>({
    ticker: '',
    name: '',
    asset_class: '',
    sector: '',
    broker: '',
    purchase_date: getTodayDate(),
  });
  const [errors, setErrors] = useState<Partial<Record<keyof HoldingInput, string>>>({});
  const [searchResults, setSearchResults] = useState<TickerSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimeout = useRef<NodeJS.Timeout | null>(null);

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

  // Debounced ticker search
  useEffect(() => {
    if (searchQuery.length > 0) {
      setIsSearching(true);

      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }

      debounceTimeout.current = setTimeout(async () => {
        try {
          const results = await searchTickers(searchQuery, 10);
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
  }, [searchQuery]);

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

  const handleTickerInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    setFormData((prev) => ({ ...prev, ticker: value }));

    if (errors.ticker) {
      setErrors((prev) => ({ ...prev, ticker: undefined }));
    }
  };

  const handleSelectTicker = (result: TickerSearchResult) => {
    setFormData((prev) => ({
      ...prev,
      ticker: result.ticker,
      name: result.name,
      asset_class: result.asset_class,
      sector: result.category || '',
    }));
    setSearchQuery(result.ticker);
    setShowDropdown(false);
    setSearchResults([]);

    // Clear relevant errors
    setErrors((prev) => ({
      ...prev,
      ticker: undefined,
      name: undefined,
      asset_class: undefined,
      sector: undefined,
    }));
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when field is modified
    if (errors[name as keyof HoldingInput]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    const success = await onSubmit({
      ...formData,
      ticker: formData.ticker.toUpperCase().trim(),
      name: formData.name.trim(),
      broker: formData.broker.trim(),
    });

    if (success) {
      // Reset form on success
      setFormData({
        ticker: '',
        name: '',
        asset_class: '',
        sector: '',
        broker: '',
        purchase_date: getTodayDate(),
      });
    }
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <h3 className={styles.title}>Add New Holding</h3>

      <div className={styles.formGrid}>
        <div className={styles.field} style={{ position: 'relative' }}>
          <label htmlFor="ticker" className={styles.label}>
            Ticker Symbol
          </label>
          <input
            type="text"
            id="ticker"
            name="ticker"
            value={formData.ticker}
            onChange={handleTickerInputChange}
            className={`${styles.input} ${errors.ticker ? styles.inputError : ''}`}
            placeholder="Type to search... (e.g., VTI)"
            disabled={isSubmitting}
            autoComplete="off"
          />
          {isSearching && (
            <span className={styles.searchingIndicator}>Searching...</span>
          )}
          {errors.ticker && <span className={styles.error}>{errors.ticker}</span>}

          {showDropdown && searchResults.length > 0 && (
            <div ref={dropdownRef} className={styles.dropdown}>
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
            Name
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={`${styles.input} ${errors.name ? styles.inputError : ''}`}
            placeholder="e.g., Vanguard Total Stock Market ETF"
            disabled={isSubmitting}
          />
          {errors.name && <span className={styles.error}>{errors.name}</span>}
        </div>

        <div className={styles.field}>
          <label htmlFor="asset_class" className={styles.label}>
            Asset Class
          </label>
          <select
            id="asset_class"
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
          <label htmlFor="sector" className={styles.label}>
            Sector
          </label>
          <select
            id="sector"
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
          <label htmlFor="broker" className={styles.label}>
            Broker
          </label>
          <input
            type="text"
            id="broker"
            name="broker"
            value={formData.broker}
            onChange={handleChange}
            className={`${styles.input} ${errors.broker ? styles.inputError : ''}`}
            placeholder="e.g., Fidelity"
            disabled={isSubmitting}
          />
          {errors.broker && <span className={styles.error}>{errors.broker}</span>}
        </div>

        <div className={styles.field}>
          <label htmlFor="purchase_date" className={styles.label}>
            Purchase Date
          </label>
          <input
            type="date"
            id="purchase_date"
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
          onClick={onCancel}
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
  );
}
