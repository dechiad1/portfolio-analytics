import { useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { Position } from '../../shared/types';
import { LoadingSpinner } from '../../shared/components/LoadingSpinner';
import { ErrorMessage } from '../../shared/components/ErrorMessage';
import { usePortfolioDetailState } from './usePortfolioDetailState';
import { SummaryCards } from './components/SummaryCards';
import { BreakdownCharts } from './components/BreakdownCharts';
import { PositionsTable } from './components/PositionsTable';
import { AddPositionModal } from './components/AddPositionModal';
import { RiskAnalysisSection } from './components/RiskAnalysisSection';
import { SimulationsSection } from './components/SimulationsSection';
import styles from './PortfolioDetailPage.module.css';

/**
 * PortfolioDetailPage displays a portfolio's details, positions, and analytics.
 */
export function PortfolioDetailPage() {
  const { id: portfolioId } = useParams<{ id: string }>();

  const {
    portfolio,
    summary,
    positions,
    transactions,
    isLoading,
    error,
    isMutating,
    refetch,
    addPosition,
    removePosition,
    clearError,
    // Risk analysis state
    riskAnalysis,
    riskAnalysisList,
    isGeneratingRiskAnalysis,
    isLoadingAnalysis,
    isDeletingAnalysis,
    runRiskAnalysis,
    selectAnalysis,
    removeAnalysis,
  } = usePortfolioDetailState(portfolioId!);

  const [showAddModal, setShowAddModal] = useState(false);

  const handleAddClick = useCallback(() => {
    setShowAddModal(true);
    clearError();
  }, [clearError]);

  const handleCloseAdd = useCallback(() => {
    setShowAddModal(false);
  }, []);

  const handleDelete = useCallback(
    async (position: Position) => {
      const confirmed = window.confirm(
        `Are you sure you want to remove ${position.ticker}?`
      );
      if (confirmed) {
        await removePosition(position.security_id);
      }
    },
    [removePosition]
  );

  if (isLoading) {
    return (
      <div className={styles.page}>
        <LoadingSpinner size="large" message="Loading portfolio..." />
      </div>
    );
  }

  if (error && !portfolio) {
    return (
      <div className={styles.page}>
        <ErrorMessage message={error} onRetry={refetch} />
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className={styles.page}>
        <ErrorMessage message="Portfolio not found" />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>
        <Link to="/portfolios" className={styles.breadcrumbLink}>
          Portfolios
        </Link>
        <span className={styles.breadcrumbSeparator}>/</span>
        <span className={styles.breadcrumbCurrent}>{portfolio.name}</span>
      </div>

      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>{portfolio.name}</h1>
          <p className={styles.description}>Currency: {portfolio.base_currency}</p>
        </div>
        <button
          className={styles.addButton}
          onClick={handleAddClick}
          disabled={isMutating}
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
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>Add Position</span>
        </button>
      </div>

      {error && (
        <div className={styles.errorContainer}>
          <ErrorMessage
            message={error}
            onRetry={() => {
              clearError();
              refetch();
            }}
          />
        </div>
      )}

      {summary && positions.length > 0 && (
        <>
          <section className={styles.section}>
            <SummaryCards summary={summary} />
          </section>

          <section className={styles.section}>
            <BreakdownCharts summary={summary} />
          </section>
        </>
      )}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Positions</h2>
        <PositionsTable
          positions={positions}
          onDelete={handleDelete}
          isDisabled={isMutating}
        />
      </section>

      <section className={styles.section}>
        <RiskAnalysisSection
          riskAnalysis={riskAnalysis}
          riskAnalysisList={riskAnalysisList}
          isGenerating={isGeneratingRiskAnalysis}
          isLoadingAnalysis={isLoadingAnalysis}
          isDeletingAnalysis={isDeletingAnalysis}
          onGenerate={runRiskAnalysis}
          onSelectAnalysis={selectAnalysis}
          onDeleteAnalysis={removeAnalysis}
          hasHoldings={positions.length > 0}
        />
      </section>

      <section className={styles.section}>
        <SimulationsSection
          portfolioId={portfolioId!}
          hasHoldings={positions.length > 0}
        />
      </section>

      {showAddModal && (
        <AddPositionModal
          onSubmit={addPosition}
          onClose={handleCloseAdd}
          isSubmitting={isMutating}
        />
      )}
    </div>
  );
}
