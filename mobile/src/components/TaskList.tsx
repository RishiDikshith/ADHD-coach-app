import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Vibration,
} from "react-native";
import { CheckSquare, Square, Zap, EyeOff, Sparkles, Plus, Trash2 } from "lucide-react-native";
import { useUserStore } from "../store/userStore";
import { useAnalyzeTaskMutation } from "../api/queries";
import type { ADHDTask } from "../api/types";

interface TaskListProps {
  tasks: ADHDTask[];
  onToggleComplete: (id: string) => void;
  onAddTask: (title: string, energy: number) => void;
  onDeleteTask: (id: string) => void;
  onBreakdownTask: (id: string, subtasks: ADHDTask[]) => void;
}

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  onToggleComplete,
  onAddTask,
  onDeleteTask,
  onBreakdownTask,
}) => {
  const user = useUserStore();
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [selectedEnergy, setSelectedEnergy] = useState<number>(3); // 1-5 Scale
  
  // Custom ADHD UX states
  const [filterEnergy, setFilterEnergy] = useState<number | null>(null);
  const [overwhelmMode, setOverwhelmMode] = useState(false);
  const [breakingTaskId, setBreakingTaskId] = useState<string | null>(null);

  const breakdownMutation = useAnalyzeTaskMutation();

  const handleAddTask = () => {
    if (!newTaskTitle.trim()) return;
    onAddTask(newTaskTitle.trim(), selectedEnergy);
    setNewTaskTitle("");
    setSelectedEnergy(3);
  };

  const handleToggle = (id: string) => {
    onToggleComplete(id);
    Vibration.vibrate(80); // Quick haptic tap for dopamine reinforcement
  };

  const handleStartTinyAI = async (task: ADHDTask) => {
    setBreakingTaskId(task.id);
    try {
      const result = await breakdownMutation.mutateAsync({
        taskDescription: task.title,
        userData: {
          sleep_hours: 7,
          stress_level: overwhelmMode ? 9 : 4,
          phone_distractions: 2,
        },
      });

      // Parse generated micro-steps (e.g. from the backend Task Paralysis engine)
      if (result && Array.isArray(result.microtasks)) {
        const generatedTasks: ADHDTask[] = result.microtasks.map((step: string, index: number) => ({
          id: `${task.id}-sub-${index}`,
          title: step,
          completed: false,
          created_at: new Date().toISOString(),
        }));
        onBreakdownTask(task.id, generatedTasks);
      }
    } catch (e) {
      console.error("AI breakdown error:", e);
    } finally {
      setBreakingTaskId(null);
    }
  };

  // Filter tasks based on energy level selection
  const filteredTasks = tasks.filter((t) => {
    if (t.completed) return true; // Keep completed tasks in list
    if (filterEnergy !== null && t.energy_required !== undefined) {
      return t.energy_required <= filterEnergy;
    }
    return true;
  });

  // Overwhelm Mode Selection: Find the first uncompleted task
  const singleFocusTask = filteredTasks.find((t) => !t.completed);

  return (
    <View style={styles.container}>
      {/* 1. ADHD Controls: Overwhelm Mode & Energy Slider */}
      <View style={styles.adhdControllerRow}>
        <TouchableOpacity
          style={[styles.overwhelmToggle, overwhelmMode && styles.overwhelmActive]}
          onPress={() => setOverwhelmMode(!overwhelmMode)}
        >
          <EyeOff size={16} color={overwhelmMode ? "#fff" : "#fb923c"} />
          <Text style={[styles.controlText, overwhelmMode && { color: "#fff" }]}>
            {overwhelmMode ? "Overwhelm: ON (Calming)" : "Overwhelm Mode"}
          </Text>
        </TouchableOpacity>

        {/* Horizontal Energy filter tabs */}
        <View style={styles.energyFilters}>
          <Text style={styles.energyLabel}>Energy:</Text>
          {[1, 3, 5].map((lvl) => (
            <TouchableOpacity
              key={lvl}
              style={[
                styles.energyBadge,
                filterEnergy === lvl && styles.energyBadgeActive,
              ]}
              onPress={() => setFilterEnergy(filterEnergy === lvl ? null : lvl)}
            >
              <Zap size={10} color={filterEnergy === lvl ? "#000" : "#6366f1"} />
              <Text
                style={[
                  styles.energyBadgeText,
                  filterEnergy === lvl && { color: "#000" },
                ]}
              >
                {lvl === 1 ? "Low" : lvl === 3 ? "Med" : "High"}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* 2. OVERWHELM MODE CALM UI SCREEN */}
      {overwhelmMode ? (
        <View style={styles.calmFocusCard}>
          {singleFocusTask ? (
            <View style={{ alignItems: "center", width: "100%" }}>
              <Text style={styles.calmHelpHeader}>Just do this single tiny step. Ignore the rest:</Text>
              
              <View style={styles.calmTaskMainRow}>
                <TouchableOpacity onPress={() => handleToggle(singleFocusTask.id)}>
                  <Square size={28} color="#6366f1" />
                </TouchableOpacity>
                <Text style={styles.calmTaskTitle}>{singleFocusTask.title}</Text>
              </View>

              {/* Energy rating */}
              <View style={styles.calmEnergyRow}>
                <Zap size={14} color="#fbbf24" />
                <Text style={styles.calmEnergyText}>
                  Energy level: {singleFocusTask.energy_required || 3}/5
                </Text>
              </View>

              {/* Start Tiny AI Assistant for overwhelm */}
              <TouchableOpacity
                style={styles.calmAiBtn}
                onPress={() => handleStartTinyAI(singleFocusTask)}
                disabled={breakingTaskId !== null}
              >
                <Sparkles size={16} color="#fff" style={{ marginRight: 6 }} />
                {breakingTaskId === singleFocusTask.id ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={styles.calmAiBtnText}>Decompose into 2-Minute Steps</Text>
                )}
              </TouchableOpacity>
            </View>
          ) : (
            <View style={{ alignItems: "center" }}>
              <Text style={styles.calmEmptyEmoji}>🍵</Text>
              <Text style={styles.calmEmptyText}>All clear! Your mind is free to rest.</Text>
            </View>
          )}
        </View>
      ) : (
        /* 3. STANDARD TASK VIEW */
        <ScrollView style={styles.scrollArea}>
          {/* List display */}
          <View style={styles.taskListContainer}>
            {filteredTasks.map((task) => (
              <View key={task.id} style={styles.taskCard}>
                <View style={styles.taskCoreRow}>
                  <TouchableOpacity onPress={() => handleToggle(task.id)}>
                    {task.completed ? (
                      <CheckSquare size={22} color="#10b981" />
                    ) : (
                      <Square size={22} color="#6366f1" />
                    )}
                  </TouchableOpacity>
                  
                  <View style={{ flex: 1, marginLeft: 10 }}>
                    <Text
                      style={[
                        styles.taskTitle,
                        task.completed && styles.taskTitleCompleted,
                      ]}
                    >
                      {task.title}
                    </Text>

                    {/* Show energy requirements */}
                    {!task.completed && (
                      <View style={styles.metaRow}>
                        <View style={styles.energyMeta}>
                          <Zap size={10} color="#fbbf24" />
                          <Text style={styles.metaText}>Energy: {task.energy_required || 3}</Text>
                        </View>
                      </View>
                    )}
                  </View>

                  {/* Actions column */}
                  <View style={styles.taskActionsColumn}>
                    {!task.completed && (
                      <TouchableOpacity
                        style={styles.actionTinyBtn}
                        onPress={() => handleStartTinyAI(task)}
                        disabled={breakingTaskId !== null}
                      >
                        {breakingTaskId === task.id ? (
                          <ActivityIndicator size="small" color="#818cf8" />
                        ) : (
                          <Sparkles size={14} color="#818cf8" />
                        )}
                      </TouchableOpacity>
                    )}
                    <TouchableOpacity onPress={() => onDeleteTask(task.id)}>
                      <Trash2 size={14} color="#ef4444" />
                    </TouchableOpacity>
                  </View>
                </View>

                {/* Subtask list generated by AI breakdown */}
                {task.subtasks && task.subtasks.length > 0 && (
                  <View style={styles.subtasksWrapper}>
                    <Text style={styles.subtasksHeader}>💡 2-Min Action Breakdown:</Text>
                    {task.subtasks.map((sub) => (
                      <View key={sub.id} style={styles.subtaskRow}>
                        <TouchableOpacity onPress={() => handleToggle(sub.id)}>
                          {sub.completed ? (
                            <CheckSquare size={16} color="#10b981" />
                          ) : (
                            <Square size={16} color="#4b487c" />
                          )}
                        </TouchableOpacity>
                        <Text
                          style={[
                            styles.subtaskTitle,
                            sub.completed && styles.subtaskTitleCompleted,
                          ]}
                        >
                          {sub.title}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            ))}
          </View>
        </ScrollView>
      )}

      {/* 4. TASK ENTRY DOCK (Hidden in overwhelm mode for visual minimalism) */}
      {!overwhelmMode && (
        <View style={styles.dockContainer}>
          <TextInput
            style={styles.dockInput}
            placeholder="Add a new task..."
            placeholderTextColor="#6b7280"
            value={newTaskTitle}
            onChangeText={setNewTaskTitle}
          />
          
          {/* Energy Rating picker */}
          <View style={styles.dockEnergyPicker}>
            {[1, 3, 5].map((lvl) => (
              <TouchableOpacity
                key={lvl}
                style={[
                  styles.pickerEnergyBadge,
                  selectedEnergy === lvl && styles.pickerEnergyBadgeActive,
                ]}
                onPress={() => setSelectedEnergy(lvl)}
              >
                <Zap size={10} color={selectedEnergy === lvl ? "#000" : "#fbbf24"} />
                <Text style={[styles.pickerEnergyText, selectedEnergy === lvl && { color: "#000" }]}>
                  {lvl}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={styles.dockAddBtn} onPress={handleAddTask}>
            <Plus size={20} color="#000" />
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0e26",
    width: "100%",
  },
  adhdControllerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#1e1b4b",
    backgroundColor: "#11102e",
  },
  overwhelmToggle: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#2a1b10",
    borderWidth: 1,
    borderColor: "#ea580c",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 14,
    gap: 6,
  },
  overwhelmActive: {
    backgroundColor: "#ea580c",
    borderColor: "#f97316",
  },
  controlText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#ea580c",
  },
  energyFilters: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  energyLabel: {
    fontSize: 11,
    color: "#6b7280",
    fontWeight: "700",
  },
  energyBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#1e1b4b",
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#4b487c",
    gap: 4,
  },
  energyBadgeActive: {
    backgroundColor: "#6366f1",
    borderColor: "#818cf8",
  },
  energyBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#818cf8",
  },
  calmFocusCard: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  calmHelpHeader: {
    color: "#9ca3af",
    fontSize: 14,
    textAlign: "center",
    marginBottom: 16,
  },
  calmTaskMainRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#1e1b4b",
    borderWidth: 2,
    borderColor: "#6366f1",
    borderRadius: 24,
    padding: 20,
    width: "100%",
    gap: 14,
    shadowColor: "#6366f1",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 6,
  },
  calmTaskTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: "#fff",
    flex: 1,
  },
  calmEnergyRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 16,
    backgroundColor: "#1e1b4b",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 12,
  },
  calmEnergyText: {
    color: "#fbbf24",
    fontSize: 12,
    fontWeight: "700",
  },
  calmAiBtn: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#6366f1",
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 16,
    marginTop: 32,
    shadowColor: "#6366f1",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
  },
  calmAiBtnText: {
    color: "#fff",
    fontSize: 13,
    fontWeight: "800",
  },
  calmEmptyEmoji: {
    fontSize: 48,
    marginBottom: 16,
  },
  calmEmptyText: {
    color: "#10b981",
    fontWeight: "700",
    fontSize: 15,
  },
  scrollArea: {
    flex: 1,
    padding: 16,
  },
  taskListContainer: {
    gap: 12,
    paddingBottom: 40,
  },
  taskCard: {
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderColor: "#1e1b4b",
    borderRadius: 18,
    padding: 14,
  },
  taskCoreRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  taskTitle: {
    color: "#f1f5f9",
    fontSize: 14,
    fontWeight: "700",
  },
  taskTitleCompleted: {
    color: "#4b487c",
    textDecorationLine: "line-through",
  },
  metaRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 4,
  },
  energyMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
  },
  metaText: {
    color: "#6b7280",
    fontSize: 10,
    fontWeight: "700",
  },
  taskActionsColumn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  actionTinyBtn: {
    padding: 6,
    borderRadius: 8,
    backgroundColor: "#1c1b3f",
  },
  subtasksWrapper: {
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#1e1b4b",
    paddingTop: 10,
    gap: 8,
  },
  subtasksHeader: {
    fontSize: 11,
    fontWeight: "800",
    color: "#818cf8",
    marginBottom: 2,
  },
  subtaskRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingLeft: 12,
    gap: 8,
  },
  subtaskTitle: {
    color: "#cbd5e1",
    fontSize: 12,
    fontWeight: "500",
  },
  subtaskTitleCompleted: {
    color: "#4b487c",
    textDecorationLine: "line-through",
  },
  dockContainer: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: "#1e1b4b",
    backgroundColor: "#11102e",
    gap: 8,
  },
  dockInput: {
    flex: 1,
    backgroundColor: "#0f0e26",
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: "#fff",
    fontSize: 13,
    borderWidth: 1,
    borderColor: "#1e1b4b",
  },
  dockEnergyPicker: {
    flexDirection: "row",
    gap: 4,
  },
  pickerEnergyBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "#1e1b4b",
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#4b487c",
  },
  pickerEnergyBadgeActive: {
    backgroundColor: "#fbbf24",
    borderColor: "#fb923c",
  },
  pickerEnergyText: {
    fontSize: 9,
    fontWeight: "900",
    color: "#fbbf24",
  },
  dockAddBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#6ee7b7",
    justifyContent: "center",
    alignItems: "center",
  },
});
