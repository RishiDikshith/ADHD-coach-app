import React from "react";
import { DarkTheme, ThemeProvider } from "@react-navigation/native";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useUserStore } from "../src/store/userStore";

// Create global QueryClient for mobile API fetching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// ADHD Custom Dark Theme
const ADHDDarkTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    primary: "#6366f1", // Iris Indigo
    background: "#0f0e26", // Space Deep Indigo
    card: "#11102e", // Lighter container indigo
    text: "#ffffff",
    border: "#1e1b4b",
    notification: "#fbbf24",
  },
};

export default function RootLayout() {
  const user = useUserStore();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider value={ADHDDarkTheme}>
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="settings" options={{ presentation: "modal", title: "ADHD settings" }} />
        </Stack>
        <StatusBar style="light" />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
