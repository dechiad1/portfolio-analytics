import type { RiskAnalysisResult } from '../../../shared/types';
import styles from './RiskAnalysisSection.module.css';

interface RiskAnalysisSectionProps {
  riskAnalysis: RiskAnalysisResult | null;
  isGenerating: boolean;
  onGenerate: () => Promise<boolean>;
  hasHoldings: boolean;
}

/**
 * RiskAnalysisSection displays AI-generated risk analysis.
 */
export function RiskAnalysisSection({
  riskAnalysis,
  isGenerating,
  onGenerate,
  hasHoldings,
}: RiskAnalysisSectionProps) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h2 className={styles.title}>AI Risk Analysis</h2>
          <p className={styles.description}>
            Generate an AI-powered analysis of your portfolio's risk profile
          </p>
        </div>
        <button
          className={styles.generateButton}
          onClick={onGenerate}
          disabled={isGenerating || !hasHoldings}
          title={!hasHoldings ? 'Add holdings to generate risk analysis' : undefined}
        >
          {isGenerating ? (
            <>
              <span className={styles.spinner} />
              Analyzing...
            </>
          ) : (
            <>
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
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
              {riskAnalysis ? 'Regenerate Analysis' : 'Generate Analysis'}
            </>
          )}
        </button>
      </div>

      {!hasHoldings && (
        <div className={styles.emptyState}>
          <svg
            className={styles.emptyIcon}
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <p className={styles.emptyText}>
            Add holdings to your portfolio to generate a risk analysis.
          </p>
        </div>
      )}

      {hasHoldings && !riskAnalysis && !isGenerating && (
        <div className={styles.placeholder}>
          <svg
            className={styles.placeholderIcon}
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="7.5 4.21 12 6.81 16.5 4.21" />
            <polyline points="7.5 19.79 7.5 14.6 3 12" />
            <polyline points="21 12 16.5 14.6 16.5 19.79" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
          <p className={styles.placeholderText}>
            Click "Generate Analysis" to get AI-powered insights about your portfolio's risk profile,
            diversification, and recommendations.
          </p>
        </div>
      )}

      {isGenerating && (
        <div className={styles.loading}>
          <div className={styles.loadingSpinner} />
          <p className={styles.loadingText}>
            Analyzing your portfolio... This may take a moment.
          </p>
        </div>
      )}

      {riskAnalysis && !isGenerating && (
        <div className={styles.result}>
          <div className={styles.resultContent}>
            {riskAnalysis.analysis.split('\n').map((paragraph, index) => (
              <p key={index} className={styles.paragraph}>
                {paragraph}
              </p>
            ))}
          </div>
          <p className={styles.timestamp}>
            Generated on {new Date(riskAnalysis.generated_at).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}
