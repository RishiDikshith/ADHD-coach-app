"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, useSyncExternalStore, type ReactNode } from "react";
import { useUserStore } from "@/stores/user-store";

const subscribeHydration = (callback: () => void) => {
  if (!useUserStore.persist?.onFinishHydration) {
    return () => {};
  }
  return useUserStore.persist.onFinishHydration(callback);
};

const getHydrationSnapshot = () => useUserStore.persist?.hasHydrated?.() ?? false;
const getServerSnapshot = () => false;

export function Providers({ children }: { children: ReactNode }) {
  const initializeAuth = useUserStore((state) => state.initializeAuth);
  const hydrated = useSyncExternalStore(
    subscribeHydration,
    getHydrationSnapshot,
    getServerSnapshot
  );
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
    if (hydrated) void initializeAuth();
  }, [hydrated, initializeAuth]);

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
