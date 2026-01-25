import { useCallback, useEffect } from 'react';
import { useSpeechRecognition } from '../../../shared/hooks/useSpeechRecognition';
import styles from './DictationInput.module.css';

interface DictationInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function DictationInput({ value, onChange, disabled = false }: DictationInputProps) {
  const handleResult = useCallback(
    (result: { transcript: string }) => {
      onChange(value + (value ? ' ' : '') + result.transcript);
    },
    [value, onChange]
  );

  const {
    isListening,
    isSupported,
    startListening,
    stopListening,
    error: speechError,
  } = useSpeechRecognition({
    onResult: handleResult,
    continuous: true,
    interimResults: true,
  });

  // Stop listening when disabled
  useEffect(() => {
    if (disabled && isListening) {
      stopListening();
    }
  }, [disabled, isListening, stopListening]);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  return (
    <div className={styles.container}>
      <label htmlFor="description" className={styles.label}>
        Describe Your Portfolio <span className={styles.required}>*</span>
      </label>
      <div className={styles.inputWrapper}>
        <textarea
          id="description"
          className={styles.textarea}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Example: I want 60% in S&P 500, 20% in international stocks, and 20% in bonds..."
          disabled={disabled}
          rows={4}
        />
        {isSupported && (
          <button
            type="button"
            className={`${styles.micButton} ${isListening ? styles.listening : ''}`}
            onClick={toggleListening}
            disabled={disabled}
            aria-label={isListening ? 'Stop recording' : 'Start voice input'}
            title={isListening ? 'Stop recording' : 'Click to speak'}
          >
            {isListening ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
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
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            )}
          </button>
        )}
      </div>
      {isListening && (
        <p className={styles.listeningIndicator}>
          <span className={styles.pulsingDot} />
          Listening... Speak now
        </p>
      )}
      {speechError && <p className={styles.error}>{speechError}</p>}
      {!isSupported && (
        <p className={styles.hint}>
          Voice input is not supported in this browser. Please type your description.
        </p>
      )}
      <p className={styles.hint}>
        Describe your ideal portfolio allocation. Include percentages and asset types like stocks,
        bonds, or specific tickers.
      </p>
    </div>
  );
}
