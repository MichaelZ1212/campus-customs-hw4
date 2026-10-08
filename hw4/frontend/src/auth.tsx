import { createContext, ReactNode, useContext, useState } from "react";

export interface AuthUser { id: number; first_name: string; last_name: string; email: string; }
export interface AuthSession { user: AuthUser; access_token: string; }
interface AuthContextValue { user: AuthUser | null; token: string | null; signIn: (session: AuthSession) => void; signOut: () => void; }

const STORAGE_KEY = "campus_customs_user";
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function storedSession(): AuthSession | null {
  try {
    const value = sessionStorage.getItem(STORAGE_KEY);
    const parsed = value ? JSON.parse(value) as Partial<AuthSession> : null;
    return parsed?.user && parsed.access_token ? parsed as AuthSession : null;
  } catch { return null; }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(storedSession);
  const signIn = (nextSession: AuthSession) => { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession)); setSession(nextSession); };
  const signOut = () => { sessionStorage.removeItem(STORAGE_KEY); setSession(null); };
  return <AuthContext.Provider value={{ user: session?.user ?? null, token: session?.access_token ?? null, signIn, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
