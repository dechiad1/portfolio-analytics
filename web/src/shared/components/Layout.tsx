import { Outlet } from 'react-router-dom';
import { Navigation } from './Navigation';
import styles from './Layout.module.css';

/**
 * Layout component provides the main application structure
 * including header with navigation and main content area.
 */
export function Layout() {
  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.logoSection}>
            <svg
              className={styles.logoIcon}
              xmlns="http://www.w3.org/2000/svg"
              width="28"
              height="28"
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
            <h1 className={styles.logoText}>Portfolio Analytics</h1>
          </div>
          <Navigation />
        </div>
      </header>
      <main className={styles.main}>
        <div className={styles.mainContent}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
