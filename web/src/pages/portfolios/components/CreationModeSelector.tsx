import type { CreationMode } from '../../../shared/types';
import styles from './CreationModeSelector.module.css';

interface CreationModeSelectorProps {
  value: CreationMode;
  onChange: (mode: CreationMode) => void;
  disabled?: boolean;
}

const MODE_OPTIONS: { value: CreationMode; label: string; description: string }[] = [
  {
    value: 'empty',
    label: 'Empty Portfolio',
    description: 'Start with an empty portfolio and add holdings manually',
  },
  {
    value: 'random',
    label: 'Random Allocation',
    description: 'Generate a diversified portfolio with random securities',
  },
  {
    value: 'dictation',
    label: 'Tell Us About Your Assets',
    description: 'Describe your portfolio and we will allocate securities for you',
  },
];

export function CreationModeSelector({
  value,
  onChange,
  disabled = false,
}: CreationModeSelectorProps) {
  return (
    <div className={styles.container}>
      <span className={styles.label}>Portfolio Type</span>
      <div className={styles.options}>
        {MODE_OPTIONS.map((option) => (
          <label
            key={option.value}
            className={`${styles.option} ${value === option.value ? styles.selected : ''} ${disabled ? styles.disabled : ''}`}
          >
            <input
              type="radio"
              name="creationMode"
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              disabled={disabled}
              className={styles.radio}
            />
            <div className={styles.optionContent}>
              <span className={styles.optionLabel}>{option.label}</span>
              <span className={styles.optionDescription}>{option.description}</span>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
}
