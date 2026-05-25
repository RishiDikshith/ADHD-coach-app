import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { TaskList } from "../../src/components/TaskList";
import { useUserStore } from "../../src/store/userStore";
import type { ADHDTask } from "../../src/api/types";

export default function TasksScreen() {
  const user = useUserStore();

  // Seed standard ADHD low, medium, and high energy tasks
  const [tasks, setTasks] = useState<ADHDTask[]>([
    {
      id: "seed-1",
      title: "Log daily energy check-in",
      energy_required: 1,
      completed: false,
      created_at: new Date().toISOString(),
    },
    {
      id: "seed-2",
      title: "Outline next milestone draft",
      energy_required: 5,
      completed: false,
      created_at: new Date().toISOString(),
      subtasks: [
        {
          id: "sub-seed-1",
          title: "Write down 3 rough bullets on paper",
          completed: false,
          created_at: new Date().toISOString(),
        },
      ],
    },
    {
      id: "seed-3",
      title: "Review analytics insights",
      energy_required: 3,
      completed: true,
      created_at: new Date().toISOString(),
    },
  ]);

  const handleToggleComplete = (id: string) => {
    setTasks((prev) =>
      prev.map((t) => {
        // Toggle parent task
        if (t.id === id) {
          const nowCompleted = !t.completed;
          if (nowCompleted) {
            user.completeTask();
            user.addPoints(10); // Reward 10 XP for task completion!
          }
          return {
            ...t,
            completed: nowCompleted,
            completed_at: nowCompleted ? new Date().toISOString() : undefined,
          };
        }
        
        // Toggle child subtasks
        if (t.subtasks) {
          const updatedSub = t.subtasks.map((sub) => {
            if (sub.id === id) {
              const subCompleted = !sub.completed;
              if (subCompleted) {
                user.addPoints(3); // Reward 3 XP for tiny step action!
              }
              return { ...sub, completed: subCompleted };
            }
            return sub;
          });
          return { ...t, subtasks: updatedSub };
        }

        return t;
      })
    );
  };

  const handleAddTask = (title: string, energy: number) => {
    const newTask: ADHDTask = {
      id: `task-${Date.now()}`,
      title,
      energy_required: energy,
      completed: false,
      created_at: new Date().toISOString(),
    };
    setTasks((prev) => [newTask, ...prev]);
  };

  const handleDeleteTask = (id: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== id));
  };

  const handleBreakdownTask = (parentId: string, generatedSubtasks: ADHDTask[]) => {
    setTasks((prev) =>
      prev.map((t) => {
        if (t.id === parentId) {
          return {
            ...t,
            subtasks: [...(t.subtasks || []), ...generatedSubtasks],
          };
        }
        return t;
      })
    );
    user.addPoints(5); // +5 XP dopamine bonus for breaking down overwhelm!
  };

  return (
    <View style={styles.container}>
      <TaskList
        tasks={tasks}
        onToggleComplete={handleToggleComplete}
        onAddTask={handleAddTask}
        onDeleteTask={handleDeleteTask}
        onBreakdownTask={handleBreakdownTask}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0e26",
  },
});
