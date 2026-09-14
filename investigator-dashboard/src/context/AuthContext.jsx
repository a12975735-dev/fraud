import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  /**
   * login(jwtToken, username, role, demoMode)
   * Store JWT in React state only — not in localStorage (per GDPR data minimisation §5.4).
   * demoMode=true activates synthetic fallback responses across all components.
   */
  const login = (jwtToken, username, role = 'INVESTIGATOR', demoMode = false) => {
    setToken(jwtToken);
    setUser({ username, role });
    setIsDemoMode(demoMode);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setIsDemoMode(false);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isDemoMode,
        isAuthenticated: !!token,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
