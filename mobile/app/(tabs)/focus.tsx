import React from "react";
import { StyleSheet, Text, View, ScrollView } from "react-native";
import { PomodoroTimer } from "../../src/components/PomodoroTimer";
import { Flame } from "lucide-react-native";

export default function FocusScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.header}>
        <Flame size={28} color="#ef4444" />
        <Text style={styles.title}>Focus Rescue</Text>
        <Text style={styles.subtitle}>
          Block out notifications and anchor your attention with the dopamine-celebrated Pomodoro.
        </Text>
      </View>
      
      <PomodoroTimer />
      
      <View style={styles.tipCard}>
        <Text style={styles.tipHeader}>💡 ADHD Focus Tip:</Text>
        <Text style={styles.tipText}>
          If you feel friction starting, set the timer to 10 minutes. Tell yourself: "I only have to work for 10 minutes." 90% of the time, momentum will carry you forward!
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0e26",
  },
  contentContainer: {
    padding: 20,
    alignItems: "center",
    gap: 20,
  },
  header: {
    alignItems: "center",
    textAlign: "center",
    marginVertical: 12,
  },
  title: {
    fontSize: 22,
    fontWeight: "bold",
    color: "#fff",
    marginTop: 6,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 12,
    color: "#9ca3af",
    textAlign: "center",
    lineHeight: 18,
    paddingHorizontal: 20,
  },
  tipCard: {
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    borderRadius: 18,
    padding: 16,
    width: "100%",
  },
  tipHeader: {
    fontSize: 12,
    fontWeight: "bold",
    color: "#a5b4fc",
    marginBottom: 6,
  },
  tipText: {
    fontSize: 12,
    color: "#cbd5e1",
    lineHeight: 18,
  },
});
