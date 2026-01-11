import { useState, useCallback } from 'react';
import type { Holding } from '../../shared/types';
import { LoadingSpinner } from '../../shared/components/LoadingSpinner';
import { ErrorMessage } from '../../shared/components/ErrorMessage';
import { useHoldingsState } from './useHoldingsState';
import { HoldingsTable } from './components/HoldingsTable';
import { AddHoldingForm } from './components/AddHoldingForm';
import { EditHoldingModal } from './components/EditHoldingModal';
import { CsvUpload } from './components/CsvUpload';
import styles from './HoldingsPage.module.css';

/**
 * HoldingsPage displays and manages the user's portfolio holdings.
 */
export function HoldingsPage() {
  const {
    holdings,
    isLoading,
    error,
    isMutating,
    refetch,
    addHolding,
    editHolding,
    removeHolding,
    uploadCsv,
    clearError,
  } = useHoldingsState();

  const [showAddForm, setShowAddForm] = useState(false);
  const [editingHolding, setEditingHolding] = useState<Holding | null>(null);

  const handleAddClick = useCallback(() => {
    setShowAddForm(true);
    clearError();
  }, [clearError]);

  const handleCancelAdd = useCallback(() => {
    setShowAddForm(false);
  }, []);

  const handleEdit = useCallback((holding: Holding) => {
    setEditingHolding(holding);
    clearError();
  }, [clearError]);

  const handleCloseEdit = useCallback(() => {
    setEditingHolding(null);
  }, []);

  const handleDelete = useCallback(
    async (holdingId: string) => {
      const holding = holdings.find((h) => h.id === holdingId);
      if (!holding) return;

      const confirmed = window.confirm(
        `Are you sure you want to delete ${holding.ticker}?`
      );
      if (confirmed) {
        await removeHolding(holdingId);
      }
    },
    [holdings, removeHolding]
  );

  if (isLoading) {
    return (
      <div className={styles.page}>
        <LoadingSpinner size="large" message="Loading holdings..." />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Holdings</h1>
          <p className={styles.subtitle}>
            Manage your portfolio holdings. Add individual holdings or import from CSV.
          </p>
        </div>
        {!showAddForm && (
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
            <span>Add Holding</span>
          </button>
        )}
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

      {showAddForm && (
        <div className={styles.section}>
          <AddHoldingForm
            onSubmit={addHolding}
            onCancel={handleCancelAdd}
            isSubmitting={isMutating}
          />
        </div>
      )}

      <div className={styles.mainContent}>
        <div className={styles.tableSection}>
          <HoldingsTable
            holdings={holdings}
            onEdit={handleEdit}
            onDelete={handleDelete}
            isDisabled={isMutating}
          />
        </div>

        <div className={styles.uploadSection}>
          <CsvUpload onUpload={uploadCsv} isUploading={isMutating} />
        </div>
      </div>

      {editingHolding && (
        <EditHoldingModal
          holding={editingHolding}
          onSubmit={editHolding}
          onClose={handleCloseEdit}
          isSubmitting={isMutating}
        />
      )}
    </div>
  );
}
