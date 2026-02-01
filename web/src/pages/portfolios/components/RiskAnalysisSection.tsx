import type { RiskAnalysisResult, RiskAnalysisListItem, RiskItem } from '../../../shared/types';
import styles from './RiskAnalysisSection.module.css';

interface RiskAnalysisSectionProps {
  riskAnalysis: RiskAnalysisResult | null;
  riskAnalysisList: RiskAnalysisListItem[];
  isGenerating: boolean;
  isLoadingAnalysis: boolean;
  onGenerate: () => Promise<boolean>;
  onSelectAnalysis: (analysisId: string) => Promise<boolean>;
  onDeleteAnalysis: (analysisId: string) => Promise<boolean>;
  hasHoldings: boolean;
}

function getSeverityClass(severity: string): string {
  switch (severity.toLowerCase()) {
    case 'high':
      return styles.severityHigh;
    case 'medium':
      return styles.severityMedium;
    case 'low':
      return styles.severityLow;
    default:
      return styles.severityMedium;
  }
}

function RiskCard({ risk }: { risk: RiskItem }) {
  return (
    <div className={styles.riskCard}>
      <div className={styles.riskHeader}>
        <h4 className={styles.riskTitle}>{risk.title}</h4>
        <div className={styles.riskBadges}>
          <span className={`${styles.badge} ${styles.badgeCategory}`}>
            {risk.category}
          </span>
          <span className={`${styles.badge} ${styles.badgeSeverity} ${getSeverityClass(risk.severity)}`}>
            {risk.severity}
          </span>
        </div>
      </div>
      <p className={styles.riskDescription}>{risk.description}</p>
      <div className={styles.riskDetails}>
        {risk.affected_holdings.length > 0 && (
          <div className={styles.riskDetail}>
            <span className={styles.riskDetailLabel}>Affected:</span>
            <div className={styles.affectedHoldings}>
              {risk.affected_holdings.map((ticker) => (
                <span key={ticker} className={styles.holdingTag}>{ticker}</span>
              ))}
            </div>
          </div>
        )}
        <div className={styles.riskDetail}>
          <span className={styles.riskDetailLabel}>Impact:</span>
          <span className={styles.riskDetailValue}>{risk.potential_impact}</span>
        </div>
        <div className={styles.riskDetail}>
          <span className={styles.riskDetailLabel}>Mitigation:</span>
          <span className={styles.riskDetailValue}>{risk.mitigation}</span>
        </div>
      </div>
    </div>
  );
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * RiskAnalysisSection displays AI-generated risk analysis.
 */
export function RiskAnalysisSection({
  riskAnalysis,
  riskAnalysisList,
  isGenerating,
  isLoadingAnalysis,
  onGenerate,
  onSelectAnalysis,
  onDeleteAnalysis,
  hasHoldings,
}: RiskAnalysisSectionProps) {
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const analysisId = e.target.value;
    if (analysisId) {
      onSelectAnalysis(analysisId);
    }
  };

  const handleDelete = () => {
    if (riskAnalysis && window.confirm('Delete this analysis?')) {
      onDeleteAnalysis(riskAnalysis.id);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h2 className={styles.title}>AI Risk Analysis</h2>
          <p className={styles.description}>
            Generate an AI-powered analysis of your portfolio's risk profile
          </p>
        </div>
        <div className={styles.headerActions}>
          {riskAnalysisList.length > 0 && (
            <select
              className={styles.historySelect}
              value={riskAnalysis?.id || ''}
              onChange={handleSelectChange}
              disabled={isGenerating || isLoadingAnalysis}
              aria-label="Select risk analysis"
            >
              {riskAnalysisList.map((item) => (
                <option key={item.id} value={item.id}>
                  {formatDate(item.created_at)} ({item.risk_count} risks)
                </option>
              ))}
            </select>
          )}
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
                {riskAnalysis ? 'New Analysis' : 'Generate Analysis'}
              </>
            )}
          </button>
        </div>
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

      {isLoadingAnalysis && (
        <div className={styles.loading}>
          <div className={styles.loadingSpinner} />
          <p className={styles.loadingText}>Loading analysis...</p>
        </div>
      )}

      {riskAnalysis && !isGenerating && !isLoadingAnalysis && (
        <div className={styles.result}>
          {riskAnalysis.macro_climate_summary && (
            <div className={styles.macroSummary}>
              <h4 className={styles.macroTitle}>Macro Environment</h4>
              <p className={styles.macroText}>{riskAnalysis.macro_climate_summary}</p>
            </div>
          )}
          <div className={styles.risksGrid}>
            {riskAnalysis.risks.map((risk, index) => (
              <RiskCard key={index} risk={risk} />
            ))}
          </div>
          <div className={styles.footer}>
            <div className={styles.footerInfo}>
              <p className={styles.timestamp}>
                Generated on {new Date(riskAnalysis.created_at).toLocaleString()}
              </p>
              <p className={styles.modelInfo}>Model: {riskAnalysis.model_used}</p>
            </div>
            <button
              className={styles.deleteButton}
              onClick={handleDelete}
              title="Delete this analysis"
              aria-label="Delete analysis"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
