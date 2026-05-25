import React from "react";
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Switch } from "react-native";
import { useRouter } from "expo-router";
import { ArrowLeft, User, Shield, Volume2, Bell } from "lucide-react-native";
import { useUserStore } from "../src/store/userStore";

export default function SettingsScreen() {
  const router = useRouter();
  const user = useUserStore();

  const handleToggleSound = (val: boolean) => {
    user.updateSettings({ sound_enabled: val });
  };

  const handleToggleTimeBlindness = (val: boolean) => {
    user.updateSettings({ time_blindness_enabled: val });
  };

  const handleToggleOverwhelm = (val: boolean) => {
    user.updateSettings({ overwhelm_mode_enabled: val });
  };

  const handleToggleNotifications = (val: boolean) => {
    user.updateSettings({ notifications_enabled: val });
  };

  const selectTone = (tone: "encouraging" | "direct" | "gentle" | "humorous") => {
    user.updateSettings({ coach_tone: tone });
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Back Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <ArrowLeft size={20} color="#fff" />
          <Text style={styles.backText}>Save & Exit</Text>
        </TouchableOpacity>
      </View>

      {/* 1. ADHD Coaching Tone Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <User size={18} color="#a5b4fc" />
          <Text style={styles.sectionTitle}>AI Personalities & Tone</Text>
        </View>
        <Text style={styles.sectionSubtitle}>
          Adjust the emotionally intelligent response style of the 7 AI coaching agents.
        </Text>
        
        <View style={styles.toneGrid}>
          {(["gentle", "encouraging", "direct", "humorous"] as const).map((tone) => {
            const isActive = user.settings.coach_tone === tone;
            return (
              <TouchableOpacity
                key={tone}
                style={[styles.toneBadge, isActive && styles.toneBadgeActive]}
                onPress={() => selectTone(tone)}
              >
                <Text style={[styles.toneText, isActive && { color: "#000" }]}>
                  {tone.charAt(0).toUpperCase() + tone.slice(1)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* 2. ADHD Assistive Toggles */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Shield size={18} color="#a5b4fc" />
          <Text style={styles.sectionTitle}>Assistive Cognitive Filters</Text>
        </View>
        
        {/* Overwhelm Switch */}
        <View style={styles.toggleRow}>
          <View style={{ flex: 1, paddingRight: 10 }}>
            <Text style={styles.toggleLabel}>Overwhelm Mode Safeguard</Text>
            <Text style={styles.toggleDesc}>
              Hides cluttered queues and highlights a single actionable step when stress surges.
            </Text>
          </View>
          <Switch
            value={user.settings.overwhelm_mode_enabled ?? true}
            onValueChange={handleToggleOverwhelm}
            trackColor={{ false: "#1e1b4b", true: "#6366f1" }}
            thumbColor={user.settings.overwhelm_mode_enabled ? "#6ee7b7" : "#9ca3af"}
          />
        </View>

        {/* Time Blindness Switch */}
        <View style={styles.toggleRow}>
          <View style={{ flex: 1, paddingRight: 10 }}>
            <Text style={styles.toggleLabel}>Active Day Tracker</Text>
            <Text style={styles.toggleDesc}>
              Enables active day percentage bars on the Dashboard to improve grounding.
            </Text>
          </View>
          <Switch
            value={user.settings.time_blindness_enabled ?? true}
            onValueChange={handleToggleTimeBlindness}
            trackColor={{ false: "#1e1b4b", true: "#6366f1" }}
            thumbColor={user.settings.time_blindness_enabled ? "#6ee7b7" : "#9ca3af"}
          />
        </View>
      </View>

      {/* 3. Audio Sound Design */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Volume2 size={18} color="#a5b4fc" />
          <Text style={styles.sectionTitle}>Gamified Dopamine Audios</Text>
        </View>
        <View style={styles.toggleRow}>
          <View style={{ flex: 1, paddingRight: 10 }}>
            <Text style={styles.toggleLabel}>Haptic & Chime Rewards</Text>
            <Text style={styles.toggleDesc}>
              Plays encouraging tones and active vibration feedback on timer completions.
            </Text>
          </View>
          <Switch
            value={user.settings.sound_enabled ?? true}
            onValueChange={handleToggleSound}
            trackColor={{ false: "#1e1b4b", true: "#6366f1" }}
            thumbColor={user.settings.sound_enabled ? "#6ee7b7" : "#9ca3af"}
          />
        </View>
      </View>

      {/* 4. Push Alerts */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Bell size={18} color="#a5b4fc" />
          <Text style={styles.sectionTitle}>Accountability Check-ins</Text>
        </View>
        <View style={styles.toggleRow}>
          <View style={{ flex: 1, paddingRight: 10 }}>
            <Text style={styles.toggleLabel}>Expo Push Alerts</Text>
            <Text style={styles.toggleDesc}>
              Allows gentle, non-shaming streak reminders and focus encouragement.
            </Text>
          </View>
          <Switch
            value={user.settings.notifications_enabled ?? true}
            onValueChange={handleToggleNotifications}
            trackColor={{ false: "#1e1b4b", true: "#6366f1" }}
            thumbColor={user.settings.notifications_enabled ? "#6ee7b7" : "#9ca3af"}
          />
        </View>
      </View>

      <Text style={styles.versionFoot}>ADHD platform mobile App v1.0.0</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0e26",
  },
  contentContainer: {
    padding: 16,
    gap: 16,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
  },
  backBtn: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 12,
    gap: 8,
  },
  backText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
  },
  section: {
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    borderRadius: 20,
    padding: 16,
  },
  sectionHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "800",
    color: "#a5b4fc",
  },
  sectionSubtitle: {
    fontSize: 11,
    color: "#9ca3af",
    lineHeight: 16,
    marginBottom: 16,
  },
  toneGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  toneBadge: {
    flex: 1,
    minWidth: "45%",
    backgroundColor: "#1e1b4b",
    borderWidth: 1,
    borderColor: "#2e2b5c",
    paddingVertical: 10,
    borderRadius: 14,
    alignItems: "center",
  },
  toneBadgeActive: {
    backgroundColor: "#6ee7b7",
    borderColor: "#10b981",
  },
  toneText: {
    color: "#9ca3af",
    fontSize: 12,
    fontWeight: "700",
  },
  toggleRow: {
    flexDirection: "row",
    alignItems: "center",
    borderBottomWidth: 1,
    borderBottomColor: "#1e1b4b",
    paddingVertical: 12,
  },
  toggleLabel: {
    fontSize: 13,
    fontWeight: "700",
    color: "#fff",
    marginBottom: 4,
  },
  toggleDesc: {
    fontSize: 11,
    color: "#9ca3af",
    lineHeight: 15,
  },
  versionFoot: {
    color: "#6b7280",
    fontSize: 10,
    textAlign: "center",
    marginTop: 20,
    marginBottom: 40,
  },
});
