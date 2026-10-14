import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { User, Organization, TokenResponse, AuthUserDetails } from "../types";
import {
  getCurrentUser,
  loginUser,
  registerUser,
  logoutUser,
  getStoredAccessToken,
  getStoredUserDetails,
  setStoredUserDetails,
} from "../api";

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  role: string | null;
  accessToken: string | null;
  userDetails: AuthUserDetails | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  modalMode: "login" | "signup";
  userInitials: string;
  openAuthModal: (mode?: "login" | "signup") => void;
  closeAuthModal: () => void;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    orgName?: string,
    details?: AuthUserDetails
  ) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(getStoredAccessToken());
  const [userDetails, setUserDetailsState] = useState<AuthUserDetails | null>(getStoredUserDetails());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Modal display state
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [modalMode, setModalMode] = useState<"login" | "signup">("login");

  // Determine if a real user account is logged in (excluding developer fallback)
  const isAuthenticated = Boolean(
    user && user.email && user.email !== "developer@buildbuddy.local"
  );

  // Derive user initials for profile avatars
  const userInitials = React.useMemo(() => {
    if (userDetails?.name && userDetails.name.trim().length > 0) {
      const parts = userDetails.name.trim().split(/\s+/);
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return parts[0].slice(0, 2).toUpperCase();
    }
    if (user?.email && user.email !== "developer@buildbuddy.local") {
      const namePart = user.email.split("@")[0];
      return namePart.slice(0, 2).toUpperCase();
    }
    return "NK";
  }, [user, userDetails]);

  // Refresh current user session from backend
  const refreshUser = useCallback(async () => {
    try {
      const data: TokenResponse = await getCurrentUser();
      setUser(data.user);
      setOrganization(data.organization);
      setRole(data.role);
      setAccessToken(data.access_token);
    } catch {
      setUser(null);
      setOrganization(null);
      setRole(null);
      setAccessToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const openAuthModal = useCallback((mode: "login" | "signup" = "login") => {
    setModalMode(mode);
    setIsAuthModalOpen(true);
  }, []);

  const closeAuthModal = useCallback(() => {
    setIsAuthModalOpen(false);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const data: TokenResponse = await loginUser(email, password);
      setUser(data.user);
      setOrganization(data.organization);
      setRole(data.role);
      setAccessToken(data.access_token);
      setIsAuthModalOpen(false);
    },
    []
  );

  const register = useCallback(
    async (
      email: string,
      password: string,
      orgName?: string,
      details?: AuthUserDetails
    ) => {
      const data: TokenResponse = await registerUser(email, password, orgName);
      setUser(data.user);
      setOrganization(data.organization);
      setRole(data.role);
      setAccessToken(data.access_token);

      if (details) {
        setUserDetailsState(details);
        setStoredUserDetails(details);
      }

      setIsAuthModalOpen(false);
    },
    []
  );

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
    setOrganization(null);
    setRole(null);
    setAccessToken(null);
    setUserDetailsState(null);
    // Fetch default developer context if available
    try {
      const data = await getCurrentUser();
      setUser(data.user);
      setOrganization(data.organization);
    } catch {
      // Ignored
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        role,
        accessToken,
        userDetails,
        isAuthenticated,
        isLoading,
        isAuthModalOpen,
        modalMode,
        userInitials,
        openAuthModal,
        closeAuthModal,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
