import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import type { User, LoginCredentials, RegisterCredentials } from '../types';
import {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  ApiClientError,
} from '../api/client';
import { login as apiLogin, register as apiRegister, getCurrentUser } from '../api/authApi';

/**
 * Auth state and operations.
 */
interface AuthState {
  /** Current authenticated user */
  user: User | null;
  /** JWT token */
  token: string | null;
  /** Whether auth is being initialized */
  isLoading: boolean;
  /** Whether user is authenticated */
  isAuthenticated: boolean;
  /** Login with email and password */
  login: (credentials: LoginCredentials) => Promise<{ success: boolean; error?: string }>;
  /** Register a new user */
  register: (credentials: RegisterCredentials) => Promise<{ success: boolean; error?: string }>;
  /** Logout the current user */
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * AuthProvider manages authentication state and provides it to the app.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from stored token
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = getStoredToken();

      if (storedToken) {
        try {
          // Validate the token by fetching current user
          const currentUser = await getCurrentUser();
          setToken(storedToken);
          setUser(currentUser);
        } catch (err) {
          // Token is invalid or expired, clear it
          console.info('Stored token is invalid, clearing');
          clearStoredToken();
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = useCallback(
    async (credentials: LoginCredentials): Promise<{ success: boolean; error?: string }> => {
      try {
        const tokens = await apiLogin(credentials);
        setStoredToken(tokens.access_token);
        setToken(tokens.access_token);

        // Fetch the user info
        const currentUser = await getCurrentUser();
        setUser(currentUser);

        return { success: true };
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to login';
        return { success: false, error: message };
      }
    },
    []
  );

  const register = useCallback(
    async (credentials: RegisterCredentials): Promise<{ success: boolean; error?: string }> => {
      try {
        const tokens = await apiRegister(credentials);
        setStoredToken(tokens.access_token);
        setToken(tokens.access_token);

        // Fetch the user info
        const currentUser = await getCurrentUser();
        setUser(currentUser);

        return { success: true };
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to register';
        return { success: false, error: message };
      }
    },
    []
  );

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: !!user && !!token,
      login,
      register,
      logout,
    }),
    [user, token, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

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
