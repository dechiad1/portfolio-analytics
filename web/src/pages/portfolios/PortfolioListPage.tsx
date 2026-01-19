import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import type { Portfolio } from '../../shared/types';
import { LoadingSpinner } from '../../shared/components/LoadingSpinner';
import { ErrorMessage } from '../../shared/components/ErrorMessage';
import { usePortfolioListState } from './usePortfolioListState';
import { CreatePortfolioModal } from './components/CreatePortfolioModal';
import styles from './PortfolioListPage.module.css';

/**
 * PortfolioListPage displays the user's portfolios and allows creating new ones.
 */
export function PortfolioListPage() {
  const {
    portfolios,
    isLoading,
    error,
    isMutating,
    refetch,
    addPortfolio,
    removePortfolio,
    clearError,
  } = usePortfolioListState();

  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleCreateClick = useCallback(() => {
    setShowCreateModal(true);
    clearError();
  }, [clearError]);

  const handleCloseModal = useCallback(() => {
    setShowCreateModal(false);
  }, []);

  const handleDelete = useCallback(
    async (portfolio: Portfolio) => {
      const confirmed = window.confirm(
        `Are you sure you want to delete "${portfolio.name}"? This action cannot be undone.`
      );
      if (confirmed) {
        await removePortfolio(portfolio.id);
      }
    },
    [removePortfolio]
  );

  if (isLoading) {
    return (
      <div className={styles.page}>
        <LoadingSpinner size="large" message="Loading portfolios..." />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Portfolios</h1>
          <p className={styles.subtitle}>
            Manage your investment portfolios and track their performance.
          </p>
        </div>
        <button
          className={styles.createButton}
          onClick={handleCreateClick}
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
          <span>New Portfolio</span>
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

      {portfolios.length === 0 ? (
        <div className={styles.emptyState}>
          <svg
            className={styles.emptyIcon}
            xmlns="http://www.w3.org/2000/svg"
            width="64"
            height="64"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
          <h2 className={styles.emptyTitle}>No Portfolios Yet</h2>
          <p className={styles.emptyText}>
            Create your first portfolio to start tracking your investments.
          </p>
          <button className={styles.emptyButton} onClick={handleCreateClick}>
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
            Create Portfolio
          </button>
        </div>
      ) : (
        <div className={styles.grid}>
          {portfolios.map((portfolio) => (
            <div key={portfolio.id} className={styles.card}>
              <Link to={`/portfolios/${portfolio.id}`} className={styles.cardLink}>
                <div className={styles.cardHeader}>
                  <svg
                    className={styles.cardIcon}
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
                    <line x1="12" y1="20" x2="12" y2="10" />
                    <line x1="18" y1="20" x2="18" y2="4" />
                    <line x1="6" y1="20" x2="6" y2="16" />
                  </svg>
                  <h3 className={styles.cardTitle}>{portfolio.name}</h3>
                </div>
                {portfolio.description && (
                  <p className={styles.cardDescription}>{portfolio.description}</p>
                )}
                <p className={styles.cardDate}>
                  Created {new Date(portfolio.created_at).toLocaleDateString()}
                </p>
              </Link>
              <button
                className={styles.deleteButton}
                onClick={(e) => {
                  e.preventDefault();
                  handleDelete(portfolio);
                }}
                disabled={isMutating}
                aria-label={`Delete ${portfolio.name}`}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
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
          ))}
        </div>
      )}

      {showCreateModal && (
        <CreatePortfolioModal
          onSubmit={addPortfolio}
          onClose={handleCloseModal}
          isSubmitting={isMutating}
        />
      )}
    </div>
  );
}
