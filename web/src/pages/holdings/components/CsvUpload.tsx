import { useState, useRef, useCallback } from 'react';
import styles from './CsvUpload.module.css';

interface CsvUploadProps {
  /** Callback when file is uploaded */
  onUpload: (file: File) => Promise<{ success: boolean; count?: number; error?: string }>;
  /** Whether upload is in progress */
  isUploading?: boolean;
}

/**
 * CsvUpload provides a drag-and-drop or click-to-upload
 * interface for CSV files.
 */
export function CsvUpload({ onUpload, isUploading = false }: CsvUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const validateFile = (file: File): boolean => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setResult({ type: 'error', message: 'Please select a CSV file' });
      return false;
    }
    return true;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setResult(null);

    const file = e.dataTransfer.files[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setResult(null);
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  }, []);

  const handleBrowseClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;

    setResult(null);
    const uploadResult = await onUpload(selectedFile);

    if (uploadResult.success) {
      setResult({
        type: 'success',
        message: `Successfully imported ${uploadResult.count} holding${uploadResult.count !== 1 ? 's' : ''}`,
      });
      setSelectedFile(null);
    } else {
      setResult({
        type: 'error',
        message: uploadResult.error || 'Upload failed',
      });
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setResult(null);
  };

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Import from CSV</h3>

      <div
        className={`${styles.dropzone} ${isDragging ? styles.dragging : ''} ${
          isUploading ? styles.disabled : ''
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={!selectedFile && !isUploading ? handleBrowseClick : undefined}
        role="button"
        tabIndex={!selectedFile && !isUploading ? 0 : -1}
        aria-label="Upload CSV file"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileSelect}
          className={styles.fileInput}
          disabled={isUploading}
        />

        {selectedFile ? (
          <div className={styles.selectedFile}>
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
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            <span className={styles.fileName}>{selectedFile.name}</span>
            <button
              className={styles.clearButton}
              onClick={(e) => {
                e.stopPropagation();
                handleClearFile();
              }}
              disabled={isUploading}
              aria-label="Remove file"
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
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        ) : (
          <>
            <svg
              className={styles.uploadIcon}
              xmlns="http://www.w3.org/2000/svg"
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className={styles.dropzoneText}>
              <span className={styles.dropzoneHighlight}>Click to upload</span> or
              drag and drop
            </p>
            <p className={styles.dropzoneSubtext}>CSV files only</p>
          </>
        )}
      </div>

      {selectedFile && (
        <button
          className={styles.uploadButton}
          onClick={handleUpload}
          disabled={isUploading}
        >
          {isUploading ? 'Uploading...' : 'Upload CSV'}
        </button>
      )}

      {result && (
        <div
          className={`${styles.result} ${
            result.type === 'success' ? styles.success : styles.error
          }`}
          role="alert"
        >
          {result.type === 'success' ? (
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
              <polyline points="20 6 9 17 4 12" />
            </svg>
          ) : (
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
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          )}
          <span>{result.message}</span>
        </div>
      )}

      <p className={styles.hint}>
        CSV should have columns: ticker, name, asset_class, sector, broker, purchase_date
      </p>
    </div>
  );
}
