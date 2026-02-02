import { useContext } from 'react';
import { AuthContext, type AuthState } from '../contexts/authContextDef';

/**
 * Hook to access auth state and operations.
 * Must be used within an AuthProvider.
 */
export function useAuth(): AuthState {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
