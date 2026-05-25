import React, { useState, useEffect } from "react";
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  Vibration,
} from "react-native";
import { useRouter } from "expo-router";
import { Zap, Trophy, Flame, Settings as SettingsIcon, Clock } from "lucide-react-native";
import { useUserStore } from "../../src/store/userStore";
import { MOODS } from "../../src/api/types";

export default function DashboardScreen() {
  const router = useRouter();
  const user = useUserStore();

  // Dynamic Time Blindness calculation
  const [dayProgress, setDayProgress] = useState(0);
  const [hoursRemaining, setHoursRemaining] = useState(0);

  useEffect(() => {
    const calculateDay = () => {
      const now = new Date();
      // Assume a default awake window from 7 AM to 11 PM (16 awake hours)
      const awakeStart = 7;
      const awakeEnd = 23;
      const totalAwakeSecs = (awakeEnd - awakeStart) * 3600;

      const currentHour = now.getHours();
      if (currentHour < awakeStart) {
        setDayProgress(0);
        setHoursRemaining(awakeEnd - awakeStart);
      } else if (currentHour >= awakeEnd) {
        setDayProgress(100);
        setHoursRemaining(0);
      } else {
        const secondsPassed =
          (currentHour - awakeStart) * 3600 +
          now.getMinutes() * 60 +
          now.getSeconds();
        const progress = Math.round((secondsPassed / totalAwakeSecs) * 100);
        const hoursLeft = Math.max(0, awakeEnd - currentHour);
        setDayProgress(progress);
        setHoursRemaining(hoursLeft);
      }
    };

    calculateDay();
    const interval = setInterval(calculateDay, 60000); // refresh every minute
    return () => clearInterval(interval);
  }, []);

  const handleMoodSelect = (mood: typeof MOODS[number]) => {
    user.addPoints(5); // Reward 5 XP for emotional self-regulation check-in!
    Vibration.vibrate(50);
    alert(`Logged mood: ${mood.emoji} ${mood.label}. +5 XP gained!`);
  };

  const xpProgress = user.game.points % 100;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      
      {/* 1. Time Blindness Visual Day-Progress Bar */}
      <View style={styles.timeBlindnessCard}>
        <View style={styles.cardHeaderRow}>
          <Clock size={18} color="#a5b4fc" />
          <Text style={styles.cardHeaderTitle}>Time Blindness Helper</Text>
        </View>
        <Text style={styles.dayPercentText}>{dayProgress}% of your active day is complete</Text>
        
        {/* Progress tracks */}
        <View style={styles.dayTrack}>
          <View style={[styles.dayFill, { width: `${dayProgress}%` }]} />
        </View>
        
        <Text style={styles.dayTimeLeft}>
          You have approximately <Text style={{ color: "#fff", fontWeight: "700" }}>{hoursRemaining} hours</Text> of awake focus left today.
        </Text>
      </View>

      {/* 2. Gamified Dopamine Reward Header (XP, Level, Streak) */}
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Flame size={24} color="#f97316" />
          <Text style={styles.statVal}>{user.game.streak} Days</Text>
          <Text style={styles.statLabel}>Current Streak</Text>
        </View>

        <View style={styles.statCard}>
          <Trophy size={24} color="#fbbf24" />
          <Text style={styles.statVal}>Level {user.game.level}</Text>
          <Text style={styles.statLabel}>Active Skill Tier</Text>
        </View>
      </View>

      {/* XP Level Bar */}
      <View style={styles.xpCard}>
        <View style={styles.cardHeaderRow}>
          <Zap size={16} color="#fbbf24" />
          <Text style={styles.cardHeaderTitle}>XP to Level {user.game.level + 1}</Text>
          <Text style={styles.xpFractionText}>{xpProgress}/100 XP</Text>
        </View>
        <View style={styles.dayTrack}>
          <View style={[styles.xpFill, { width: `${xpProgress}%` }]} />
        </View>
      </View>

      {/* 3. Emotional self-regulation 1-Tap Mood Logger */}
      <View style={styles.moodCard}>
        <View style={styles.cardHeaderRow}>
          <Text style={styles.cardHeaderTitle}>How are you feeling right now?</Text>
        </View>
        <Text style={styles.moodSubtitle}>Logging helps tailor AI coaching interventions</Text>
        <View style={styles.moodGrid}>
          {MOODS.map((mood) => (
            <TouchableOpacity
              key={mood.label}
              style={styles.moodButton}
              onPress={() => handleMoodSelect(mood)}
            >
              <Text style={styles.moodEmoji}>{mood.emoji}</Text>
              <Text style={styles.moodText}>{mood.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* 4. Settings shortcut buttons */}
      <View style={styles.actionCard}>
        <Text style={styles.actionTitle}>Daily Accomplishments</Text>
        <Text style={styles.actionDesc}>
          Focus Pomodoros complete: {user.game.session_count} (
          {user.game.total_focus_minutes} mins)
        </Text>
        <Text style={styles.actionDesc}>Tasks complete: {user.game.tasks_completed}</Text>
        
        <TouchableOpacity
          style={styles.settingsBtn}
          onPress={() => router.push("/settings")}
        >
          <SettingsIcon size={16} color="#9ca3af" style={{ marginRight: 6 }} />
          <Text style={styles.settingsBtnText}>Personalize Coach Settings</Text>
        </TouchableOpacity>
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
    padding: 16,
    gap: 16,
  },
  timeBlindnessCard: {
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    borderRadius: 20,
    padding: 16,
  },
  cardHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
    gap: 8,
  },
  cardHeaderTitle: {
    fontSize: 13,
    fontWeight: "800",
    color: "#a5b4fc",
    letterSpacing: 0.5,
  },
  dayPercentText: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 10,
  },
  dayTrack: {
    height: 10,
    backgroundColor: "#1e1b4b",
    borderRadius: 5,
    overflow: "hidden",
    marginBottom: 12,
  },
  dayFill: {
    height: "100%",
    backgroundColor: "#6366f1",
    borderRadius: 5,
  },
  dayTimeLeft: {
    fontSize: 11,
    color: "#9ca3af",
    lineHeight: 16,
  },
  statsGrid: {
    flexDirection: "row",
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    borderRadius: 20,
    padding: 16,
    alignItems: "center",
    gap: 4,
  },
  statVal: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#fff",
  },
  statLabel: {
    fontSize: 10,
    color: "#9ca3af",
    fontWeight: "600",
  },
  xpCard: {
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    borderRadius: 20,
    padding: 16,
  },
  xpFractionText: {
    marginLeft: "auto",
    fontSize: 11,
    color: "#fbbf24",
    fontWeight: "800",
  },
  xpFill: {
    height: "100%",
    backgroundColor: "#fbbf24",
    borderRadius: 5,
  },
  moodCard: {
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    borderRadius: 20,
    padding: 16,
  },
  moodSubtitle: {
    fontSize: 11,
    color: "#9ca3af",
    marginBottom: 16,
  },
  moodGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  moodButton: {
    flex: 1,
    minWidth: "28%",
    backgroundColor: "#1c1a3f",
    borderRadius: 14,
    paddingVertical: 10,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#2e2b5c",
  },
  moodEmoji: {
    fontSize: 22,
    marginBottom: 4,
  },
  moodText: {
    color: "#fff",
    fontSize: 11,
    fontWeight: "600",
  },
  actionCard: {
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    borderRadius: 20,
    padding: 16,
  },
  actionTitle: {
    fontSize: 14,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 8,
  },
  actionDesc: {
    fontSize: 12,
    color: "#cbd5e1",
    lineHeight: 18,
  },
  settingsBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#1e1b4b",
    borderWidth: 1,
    borderColor: "#2e2b5c",
    borderRadius: 14,
    paddingVertical: 10,
    marginTop: 16,
  },
  settingsBtnText: {
    color: "#9ca3af",
    fontSize: 12,
    fontWeight: "700",
  },
});
