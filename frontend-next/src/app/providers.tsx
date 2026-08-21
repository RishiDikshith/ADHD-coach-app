"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { useUserStore } from "@/stores/user-store";

export function Providers({ children }: { children: ReactNode }) {
  const initializeAuth = useUserStore((state) => state.initializeAuth);
  const [hydrated, setHydrated] = useState(false);
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  useEffect(() => {
    const unsubscribe = useUserStore.persist.onFinishHydration(() => setHydrated(true));
    if (useUserStore.persist.hasHydrated()) setHydrated(true);
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (hydrated) void initializeAuth();
  }, [hydrated, initializeAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
