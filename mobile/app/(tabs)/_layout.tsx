import React from "react";
import { Tabs } from "expo-router";
import { LayoutDashboard, Flame, MessageSquare, ListTodo } from "lucide-react-native";
import { useUserStore } from "../../src/store/userStore";

export default function TabLayout() {
  const user = useUserStore();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: "#6ee7b7", // Dopamine green active
        tabBarInactiveTintColor: "#9ca3af",
        tabBarStyle: {
          backgroundColor: "#11102e",
          borderTopColor: "#1e1b4b",
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
        },
        headerStyle: {
          backgroundColor: "#11102e",
          borderBottomColor: "#1e1b4b",
          borderBottomWidth: 1,
        },
        headerTitleStyle: {
          fontWeight: "bold",
          color: "#fff",
        },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Dashboard",
          tabBarLabel: "Dashboard",
          tabBarIcon: ({ color, size }) => <LayoutDashboard size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="focus"
        options={{
          title: "Focus Rescue",
          tabBarLabel: "Focus Rescue",
          tabBarIcon: ({ color, size }) => <Flame size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: "AI Co-Pilot",
          tabBarLabel: "AI Co-Pilot",
          tabBarIcon: ({ color, size }) => <MessageSquare size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="tasks"
        options={{
          title: "Calm Tasks",
          tabBarLabel: "Calm Tasks",
          tabBarIcon: ({ color, size }) => <ListTodo size={size} color={color} />,
        }}
      />
    </Tabs>
  );
}
