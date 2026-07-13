"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api } from "../lib/api";

interface User {
  id: string;
  name: string;
  email: string;
}

interface Organization {
  id: string;
  name: string;
  industry: string;
  description: string;
}

interface Workspace {
  id: string;
  organization_id: string;
  name: string;
  description: string;
  workspace_type: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  organizations: Organization[];
  workspaces: Workspace[];
  activeOrg: Organization | null;
  activeWorkspace: Workspace | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  createOrganization: (name: string, industry: string, description: string) => Promise<Organization>;
  createWorkspace: (name: string, description: string, workspaceType: string) => Promise<Workspace>;
  setActiveOrg: (org: Organization | null) => void;
  setActiveWorkspace: (ws: Workspace | null) => void;
  refreshOrgs: () => Promise<void>;
  refreshWorkspaces: (orgId: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeOrg, setActiveOrgState] = useState<Organization | null>(null);
  const [activeWorkspace, setActiveWorkspaceState] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);

  // Load token and user from localStorage on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem("token");
      if (storedToken) {
        setToken(storedToken);
        try {
          const res = await api.get("/users/me", {
            headers: { Authorization: `Bearer ${storedToken}` }
          });
          setUser(res.data);
          
          // Load active elements
          const storedOrg = localStorage.getItem("activeOrg");
          if (storedOrg) setActiveOrgState(JSON.parse(storedOrg));
          const storedWs = localStorage.getItem("activeWs");
          if (storedWs) setActiveWorkspaceState(JSON.parse(storedWs));
          
          // Initial organizations load
          const orgsRes = await api.get("/organizations/", {
            headers: { Authorization: `Bearer ${storedToken}` }
          });
          setOrganizations(orgsRes.data);
        } catch (err) {
          console.error("Token verification failed:", err);
          logout();
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  // Update active workspaces when activeOrg changes
  useEffect(() => {
    if (activeOrg) {
      refreshWorkspaces(activeOrg.id);
    } else {
      setWorkspaces([]);
      setActiveWorkspaceState(null);
    }
  }, [activeOrg]);

  const login = async (email: string, password: string) => {
    const res = await api.post("/users/login", { email, password });
    const { access_token } = res.data;
    localStorage.setItem("token", access_token);
    setToken(access_token);

    const userRes = await api.get("/users/me", {
      headers: { Authorization: `Bearer ${access_token}` }
    });
    setUser(userRes.data);

    // Load orgs
    const orgsRes = await api.get("/organizations/", {
      headers: { Authorization: `Bearer ${access_token}` }
    });
    setOrganizations(orgsRes.data);
    if (orgsRes.data.length > 0) {
      setActiveOrg(orgsRes.data[0]);
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    await api.post("/users/signup", { name, email, password });
    // Auto-login after successful registration
    await login(email, password);
  };

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("activeOrg");
    localStorage.removeItem("activeWs");
    setToken(null);
    setUser(null);
    setOrganizations([]);
    setWorkspaces([]);
    setActiveOrgState(null);
    setActiveWorkspaceState(null);
  }

  function setActiveOrg(org: Organization | null) {
    setActiveOrgState(org);
    if (org) {
      localStorage.setItem("activeOrg", JSON.stringify(org));
    } else {
      localStorage.removeItem("activeOrg");
    }
    // Clear active workspace when switching organization
    setActiveWorkspace(null);
  }

  function setActiveWorkspace(ws: Workspace | null) {
    setActiveWorkspaceState(ws);
    if (ws) {
      localStorage.setItem("activeWs", JSON.stringify(ws));
    } else {
      localStorage.removeItem("activeWs");
    }
  }

  const refreshOrgs = async () => {
    if (!token) return;
    try {
      const res = await api.get("/organizations/");
      setOrganizations(res.data);
      // Auto-set active org if not set and data exists
      if (res.data.length > 0 && !activeOrg) {
        setActiveOrg(res.data[0]);
      }
    } catch (err) {
      console.error("Failed to refresh organizations:", err);
    }
  };

  async function refreshWorkspaces(orgId: string) {
    if (!token) return;
    try {
      const res = await api.get(`/workspaces/?organization_id=${orgId}`);
      setWorkspaces(res.data);
      // Try to re-sync active workspace from current active list if possible
      if (activeWorkspace) {
        const found = res.data.find((w: Workspace) => w.id === activeWorkspace.id);
        if (!found) {
          setActiveWorkspace(res.data.length > 0 ? res.data[0] : null);
        }
      } else if (res.data.length > 0) {
        setActiveWorkspace(res.data[0]);
      }
    } catch (err) {
      console.error("Failed to refresh workspaces:", err);
    }
  }

  const createOrganization = async (name: string, industry: string, description: string) => {
    const res = await api.post("/organizations/", { name, industry, description });
    const newOrg = res.data;
    setOrganizations((prev) => [...prev, newOrg]);
    setActiveOrg(newOrg);
    return newOrg;
  };

  const createWorkspace = async (name: string, description: string, workspaceType: string) => {
    if (!activeOrg) throw new Error("No active organization selected");
    const res = await api.post("/workspaces/", {
      organization_id: activeOrg.id,
      name,
      description,
      workspace_type: workspaceType
    });
    const newWs = res.data;
    setWorkspaces((prev) => [...prev, newWs]);
    setActiveWorkspace(newWs);
    return newWs;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        organizations,
        workspaces,
        activeOrg,
        activeWorkspace,
        loading,
        login,
        signup,
        logout,
        createOrganization,
        createWorkspace,
        setActiveOrg,
        setActiveWorkspace,
        refreshOrgs,
        refreshWorkspaces
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
