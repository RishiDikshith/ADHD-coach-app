import React, { useEffect, useRef } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  AppState,
  Alert,
  Vibration,
} from "react-native";
import { Play, Pause, RotateCcw, AlertTriangle, Trophy } from "lucide-react-native";
import { useTimerStore } from "../store/timerStore";
import { useUserStore } from "../store/userStore";
import { useNotifications } from "../hooks/useNotifications";

export const PomodoroTimer: React.FC = () => {
  const timer = useTimerStore();
  const user = useUserStore();
  const { scheduleLocalNotification } = useNotifications();
  const appState = useRef(AppState.currentState);

  // Synchronous tick loop
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (timer.isActive) {
      interval = setInterval(() => {
        const didComplete = timer.tick();
        if (didComplete) {
          handleTimerCompletion();
        }
      }, 1000);
    } else {
      if (interval) clearInterval(interval);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [timer.isActive]);

  // Sync background timer state using app state changes (epoch calculation)
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextAppState) => {
      if (
        appState.current.match(/inactive|background/) &&
        nextAppState === "active"
      ) {
        // App has come to the foreground! Sync elapsed time
        const didComplete = timer.syncBackgroundTime();
        if (didComplete) {
          handleTimerCompletion();
        }
      }
      appState.current = nextAppState;
    });

    return () => {
      subscription.remove();
    };
  }, []);

  const handleTimerCompletion = async () => {
    // Reward points for deep focus
    const pointsAwarded = Math.round((timer.duration / 60) * 0.6); // ~15 points for 25m
    const { leveledUp, newLevel } = user.addPoints(pointsAwarded);
    user.incrementSession(Math.round(timer.duration / 60));

    // Heavy haptic vibration patterns to cut through ADHD hyperfocus or time blindness
    Vibration.vibrate([0, 500, 200, 500, 200, 800]);

    // Push local alert
    await scheduleLocalNotification(
      "🏆 Session Complete! Amazing focus!",
      `You completed a ${Math.round(timer.duration / 60)}m deep session and gained +${pointsAwarded} XP!`,
      1,
      { type: "timer_complete" }
    );

    let alertMsg = `Leveled up to Level ${newLevel}! Keep going!`;
    if (leveledUp) {
      Alert.alert("🎉 Level Up!", alertMsg, [{ text: "Awesome!" }]);
    } else {
      Alert.alert(
        "⚡ Focus Complete!",
        `Congratulations on staying focused for ${Math.round(
          timer.duration / 60
        )} minutes. You earned +${pointsAwarded} XP!`,
        [{ text: "Claim Points!" }]
      );
    }
  };

  const handleTogglePlay = () => {
    if (timer.isActive) {
      timer.stop();
    } else {
      timer.start();
    }
  };

  const handleReset = () => {
    timer.reset();
  };

  const handleIncrementDistraction = () => {
    timer.incrementDistractions();
    // Minor vibration for haptic feedback
    Vibration.vibrate(100);
  };

  const progressPercent = timer.getProgress() * 100;

  return (
    <View style={styles.container}>
      {/* Visual Circular/Grid Progress Display */}
      <View style={styles.progressContainer}>
        <View style={styles.outerCircle}>
          <View
            style={[
              styles.progressArc,
              { height: `${progressPercent}%`, opacity: 0.15 },
            ]}
          />
          <Text style={styles.timeText}>{timer.getFormattedTime()}</Text>
          <Text style={styles.sessionStatus}>
            {timer.isActive ? "FOCUSING" : "READY TO CHOOSE"}
          </Text>
        </View>
      </View>

      {/* Quick Session Presets */}
      <View style={styles.presetContainer}>
        {[10, 25, 45].map((mins) => (
          <TouchableOpacity
            key={mins}
            style={[
              styles.presetButton,
              timer.duration === mins * 60 && styles.activePresetButton,
            ]}
            disabled={timer.isActive}
            onPress={() => timer.setDuration(mins)}
          >
            <Text
              style={[
                styles.presetButtonText,
                timer.duration === mins * 60 && styles.activePresetButtonText,
              ]}
            >
              {mins}m
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Behavioral ADHD Distraction Tracker */}
      <TouchableOpacity
        style={styles.distractionButton}
        onPress={handleIncrementDistraction}
      >
        <AlertTriangle size={18} color="#fbbf24" style={styles.iconSpacing} />
        <Text style={styles.distractionText}>
          Log Interrupt / Mind Wander ({timer.distractions})
        </Text>
      </TouchableOpacity>

      {/* Control Actions Row */}
      <View style={styles.controlsContainer}>
        <TouchableOpacity style={styles.controlBtnReset} onPress={handleReset}>
          <RotateCcw size={24} color="#9ca3af" />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.controlBtnPlay, timer.isActive && styles.activePlayButton]}
          onPress={handleTogglePlay}
        >
          {timer.isActive ? (
            <Pause size={28} color="#000" />
          ) : (
            <Play size={28} color="#000" style={{ marginLeft: 4 }} />
          )}
        </TouchableOpacity>

        <View style={styles.xpIndicator}>
          <Trophy size={16} color="#fbbf24" />
          <Text style={styles.xpText}>+{Math.round((timer.duration / 60) * 0.6)} XP</Text>
        </View>
      </View>

      {/* Stats Footnote */}
      <Text style={styles.footnote}>
        Sessions completed today: {timer.sessionsCompleted}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#1e1b4b", // Deep calm space indigo
    padding: 24,
    borderRadius: 24,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 8,
    width: "100%",
  },
  progressContainer: {
    width: 220,
    height: 220,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 20,
  },
  outerCircle: {
    width: 200,
    height: 200,
    borderRadius: 100,
    borderWidth: 6,
    borderColor: "#4f46e5", // Vibrant dark iris
    backgroundColor: "#0f0e26",
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
    overflow: "hidden",
  },
  progressArc: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "#10b981", // Refreshing green filling
    width: "100%",
  },
  timeText: {
    fontSize: 48,
    fontVariant: ["tabular-nums"],
    fontWeight: "bold",
    color: "#fff",
  },
  sessionStatus: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 2,
    color: "#6ee7b7", // Calm emerald
    marginTop: 4,
  },
  presetContainer: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 24,
  },
  presetButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: "#2e2b5c",
    borderWidth: 1,
    borderColor: "#4b487c",
  },
  activePresetButton: {
    backgroundColor: "#4f46e5",
    borderColor: "#6366f1",
  },
  presetButtonText: {
    color: "#9ca3af",
    fontWeight: "600",
  },
  activePresetButtonText: {
    color: "#fff",
  },
  distractionButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#312e17",
    borderWidth: 1,
    borderColor: "#78350f",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 16,
    marginBottom: 24,
  },
  iconSpacing: {
    marginRight: 8,
  },
  distractionText: {
    color: "#fbbf24",
    fontSize: 13,
    fontWeight: "600",
  },
  controlsContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    width: "80%",
    marginBottom: 16,
  },
  controlBtnPlay: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: "#6ee7b7", // Satisfying dopamine completion color
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#10b981",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  activePlayButton: {
    backgroundColor: "#f87171", // Soft red to suggest pause
    shadowColor: "#ef4444",
  },
  controlBtnReset: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: "#2e2b5c",
    justifyContent: "center",
    alignItems: "center",
  },
  xpIndicator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#2e2b5c",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 12,
  },
  xpText: {
    color: "#fbbf24",
    fontWeight: "700",
    fontSize: 12,
  },
  footnote: {
    color: "#6b7280",
    fontSize: 12,
  },
});
