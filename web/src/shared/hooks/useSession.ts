import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import type { Session } from '../types';
import {
  api,
  getStoredSessionId,
  setStoredSessionId,
  ApiClientError,
} from '../api/client';

/**
 * State returned by the useSession hook.
 */
interface SessionState {
  sessionId: string | null;
  isLoading: boolean;
  error: string | null;
  refreshSession: () => Promise<void>;
}

/**
 * Context for session state to avoid prop drilling.
 */
const SessionContext = createContext<SessionState | null>(null);

/**
 * Hook to manage user session.
 * On mount, checks localStorage for existing session.
 * If none exists, creates a new session via POST /sessions.
 */
export function useSessionProvider(): SessionState {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initializeSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check for existing session in localStorage
      const storedSessionId = getStoredSessionId();

      if (storedSessionId) {
        // Validate the stored session still exists
        try {
          await api.get<Session>(`/sessions/${storedSessionId}`);
          setSessionId(storedSessionId);
          return;
        } catch (err) {
          // Session no longer valid, create a new one
          if (err instanceof ApiClientError && err.status === 404) {
            console.info('Stored session no longer valid, creating new session');
          } else {
            throw err;
          }
        }
      }

      // Create a new session
      const session = await api.post<Session>('/sessions');
      setStoredSessionId(session.id);
      setSessionId(session.id);
    } catch (err) {
      const message = err instanceof ApiClientError
        ? err.detail
        : 'Failed to initialize session';
      setError(message);
      console.error('Session initialization error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshSession = useCallback(async () => {
    await initializeSession();
  }, [initializeSession]);

  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  return {
    sessionId,
    isLoading,
    error,
    refreshSession,
  };
}

/**
 * Provider component for session context.
 */
export const SessionProvider = SessionContext.Provider;

/**
 * Hook to access session state from context.
 * Must be used within a SessionProvider.
 */
export function useSession(): SessionState {
  const context = useContext(SessionContext);

  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }

  return context;
}
