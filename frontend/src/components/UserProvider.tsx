// frontend/src/components/UserProvider.tsx

"use client";

import React, {
  createContext,
  useState,
  useEffect,
  useContext,
  ReactNode,
  useMemo,
  useCallback,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import { User } from "../types/user";

interface UserContextType {
  user: User | null;
  loading: boolean;
  refetchUser: () => void;
  logout: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

function getCookie(name: string) {
  if (typeof document === "undefined") {
    return null;
  }
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    const cookieValue = parts.pop()?.split(";").shift();
    return cookieValue;
  }
  return null;
}

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchUser = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/profiles/me/`,
        {
          credentials: "include",
        },
      );
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        setUser(null);
        if (
          pathname !== "/sign-in" &&
          pathname !== "/sign-up" &&
          pathname !== "/forgot-password" &&
          pathname !== "/verify-email" &&
          !pathname.startsWith("/reset-password/")
        ) {
          router.push("/sign-in");
        }
      }
    } catch (err) {
      console.error("me request failed", err); // eslint-disable-line no-console
      setUser(null);
      if (
        pathname !== "/sign-in" &&
        pathname !== "/sign-up" &&
        pathname !== "/forgot-password" &&
        pathname !== "/verify-email" &&
        !pathname.startsWith("/reset-password/")
      ) {
        router.push("/sign-in");
      }
    } finally {
      setLoading(false);
    }
  }, [pathname, router]);

  useEffect(() => {
    if (
      pathname !== "/sign-in" &&
      pathname !== "/sign-up" &&
      pathname !== "/forgot-password" &&
      pathname !== "/verify-email" &&
      !pathname.startsWith("/reset-password/")
    ) {
      fetchUser();
    }
  }, [fetchUser, pathname]);

  const refetchUser = useCallback(() => {
    fetchUser();
  }, [fetchUser]); // Dependency for refetchUser

  const logout = useCallback(async () => {
    const csrftoken = getCookie("csrftoken");

    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/logout/`, {
      method: "POST",
      credentials: "include",
      headers: {
        "X-CSRFToken": csrftoken || "",
        "Content-Type": "application/json",
      },
    });
    setUser(null);
    router.push("/sign-in");
  }, [router]);

  const contextValue = useMemo(
    () => ({ user, loading, refetchUser, logout }),
    [user, loading, refetchUser, logout],
  );

  return (
    <UserContext.Provider value={contextValue}>{children}</UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}
