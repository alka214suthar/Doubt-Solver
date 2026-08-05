// context/AuthContext.jsx

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { getUserDetails, logoutUser, refreshSession } from "../api/authApi";
import { clearAccessToken, setAccessToken } from "../api/tokenStore";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  const refreshUser = useCallback(async () => {
    const profile = await getUserDetails();
    setUser(profile);
    return profile;
  }, []);

  const setSession = useCallback(
    async (authResponse) => {
      setAccessToken(authResponse.access_token);
      // Prefer identity from the authenticated /users/me endpoint.
      try {
        return await refreshUser();
      } catch {
        if (authResponse.user) {
          setUser(authResponse.user);
          return authResponse.user;
        }
        clearAccessToken();
        setUser(null);
        throw new Error("Unable to load authenticated user profile");
      }
    },
    [refreshUser],
  );

  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } catch {
      // Local logout still completes if the API is temporarily unavailable.
    } finally {
      clearAccessToken();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    let active = true;

    const bootstrap = async () => {
      try {
        const authResponse = await refreshSession();
        if (!active) return;
        setAccessToken(authResponse.access_token);
        const profile = await getUserDetails();
        if (active) setUser(profile);
      } catch {
        if (active) {
          clearAccessToken();
          setUser(null);
        }
      } finally {
        if (active) setInitializing(false);
      }
    };

    bootstrap();

    const handleLogout = () => setUser(null);
    const handleRefresh = async () => {
      try {
        const profile = await getUserDetails();
        if (active) setUser(profile);
      } catch {
        if (active) setUser(null);
      }
    };
    window.addEventListener("auth:logout", handleLogout);
    window.addEventListener("auth:refreshed", handleRefresh);

    return () => {
      active = false;
      window.removeEventListener("auth:logout", handleLogout);
      window.removeEventListener("auth:refreshed", handleRefresh);
    };
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, setUser, setSession, refreshUser, logout, initializing }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
