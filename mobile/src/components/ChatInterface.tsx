import React, { useState, useRef, useEffect } from "react";
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import { Send, Volume2, Sparkles, Smile, RefreshCw } from "lucide-react-native";
import * as Speech from "expo-speech";
import { useChatStore } from "../store/chatStore";
import { useUserStore } from "../store/userStore";
import { AGENTS, MOODS } from "../api/types";

export const ChatInterface: React.FC = () => {
  const chat = useChatStore();
  const user = useUserStore();
  
  const [inputText, setInputText] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("auto");
  const [speechActive, setSpeechActive] = useState<string | null>(null);

  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    // Auto scroll to bottom when new messages arrive
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 150);
  }, [chat.messages, chat.isThinking]);

  const handleSend = async () => {
    if (!inputText.trim() || chat.isThinking) return;

    const userText = inputText;
    setInputText("");

    // Package current user scores/attributes for AI emotional context
    const currentScoreData = {
      sleep_hours: user.game.longest_streak || 7, // fallback metrics
      stress_level: user.settings.theme === "dark" ? 4 : 6,
      phone_distractions: 2,
      energy_level: 5,
    };

    await chat.sendMessage(
      userText,
      user.username || "adhd_user",
      currentScoreData,
      selectedLanguage
    );
  };

  const handleAgentSelect = (agentId: string) => {
    chat.setActiveAgentId(agentId);
  };

  const handleSpeak = (text: string, msgId: string) => {
    if (speechActive === msgId) {
      Speech.stop();
      setSpeechActive(null);
    } else {
      Speech.stop();
      setSpeechActive(msgId);
      Speech.speak(text, {
        onDone: () => setSpeechActive(null),
        onError: () => setSpeechActive(null),
      });
    }
  };

  const handleAcceptHandoff = () => {
    if (chat.handoffSuggestion) {
      chat.setActiveAgentId(chat.handoffSuggestion.agent_id);
    }
  };

  const activeAgent = AGENTS.find((a) => a.id === chat.activeAgentId) || AGENTS[0];

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
      style={styles.container}
    >
      {/* 1. Horizontal Agent Selector Panel */}
      <View style={styles.agentSelectorWrapper}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.agentSelector}
        >
          {AGENTS.map((agent) => {
            const isSelected = agent.id === chat.activeAgentId;
            return (
              <TouchableOpacity
                key={agent.id}
                style={[
                  styles.agentBtn,
                  isSelected && { borderColor: agent.color, backgroundColor: `${agent.color}15` },
                ]}
                onPress={() => handleAgentSelect(agent.id)}
              >
                <Text style={styles.agentEmoji}>{agent.emoji}</Text>
                <Text style={[styles.agentName, isSelected && { color: agent.color }]}>
                  {agent.name.split(" ")[0]}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* 2. Interactive Agent Handoff Banner */}
      {chat.handoffSuggestion && (
        <View style={styles.handoffContainer}>
          <Sparkles size={16} color="#fbbf24" style={{ marginRight: 8 }} />
          <View style={{ flex: 1 }}>
            <Text style={styles.handoffText}>
              <Text style={{ fontWeight: "700" }}>{activeAgent.name}</Text> suggests switching to{" "}
              <Text style={{ fontWeight: "700" }}>
                {AGENTS.find((a) => a.id === chat.handoffSuggestion?.agent_id)?.name}
              </Text>
              : "{chat.handoffSuggestion.message}"
            </Text>
          </View>
          <TouchableOpacity style={styles.handoffAcceptBtn} onPress={handleAcceptHandoff}>
            <Text style={styles.handoffAcceptBtnText}>Switch</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* 3. Messages Window */}
      <FlatList
        ref={flatListRef}
        data={chat.messages}
        keyExtractor={(_, index) => index.toString()}
        contentContainerStyle={styles.messageList}
        ListEmptyComponent={
          <View style={styles.welcomeContainer}>
            <Text style={styles.welcomeEmoji}>{activeAgent.emoji}</Text>
            <Text style={styles.welcomeTitle}>Chat with {activeAgent.name}</Text>
            <Text style={styles.welcomeDescription}>{activeAgent.description}</Text>
            <View style={styles.promptExamplesContainer}>
              {activeAgent.promptExamples.map((ex, i) => (
                <TouchableOpacity
                  key={i}
                  style={styles.exampleBtn}
                  onPress={() => setInputText(ex)}
                >
                  <Text style={styles.exampleText}>"{ex}"</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        }
        renderItem={({ item, index }) => {
          const isUser = item.role === "user";
          return (
            <View
              style={[
                styles.messageBubbleContainer,
                isUser ? styles.userBubbleAlign : styles.assistantBubbleAlign,
              ]}
            >
              <View
                style={[
                  styles.messageBubble,
                  isUser
                    ? styles.userBubble
                    : [styles.assistantBubble, { borderColor: activeAgent.color }],
                ]}
              >
                <Text style={isUser ? styles.userText : styles.assistantText}>
                  {item.content}
                </Text>

                {/* Subtasks or suggested interventions inside chat */}
                {item.tasks && item.tasks.length > 0 && (
                  <View style={styles.miniTasksContainer}>
                    {item.tasks.map((t, idx) => (
                      <View key={idx} style={styles.miniTaskRow}>
                        <Text style={styles.miniTaskEmoji}>{t.emoji}</Text>
                        <Text style={styles.miniTaskText}>{t.text}</Text>
                      </View>
                    ))}
                  </View>
                )}

                {/* Text-To-Speech Trigger for Assistant Bubbles */}
                {!isUser && (
                  <View style={styles.bubbleActionRow}>
                    <TouchableOpacity
                      style={styles.speakerBtn}
                      onPress={() => handleSpeak(item.content, index.toString())}
                    >
                      <Volume2
                        size={14}
                        color={speechActive === index.toString() ? "#10b981" : "#9ca3af"}
                      />
                      <Text style={[styles.speakerText, speechActive === index.toString() && { color: "#10b981" }]}>
                        {speechActive === index.toString() ? "Speaking" : "Listen"}
                      </Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            </View>
          );
        }}
      />

      {/* 4. Emotional Intelligence Shortcut Bar */}
      <View style={styles.moodSelectorContainer}>
        <Text style={styles.moodLabel}>Mood context:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.moodScroll}>
          {MOODS.map((m) => (
            <TouchableOpacity
              key={m.label}
              style={[styles.moodItem, { backgroundColor: `${m.color}15` }]}
              onPress={() => setInputText((prev) => `${prev} I feel ${m.label.toLowerCase()}...`)}
            >
              <Text style={{ fontSize: 16 }}>{m.emoji}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
        <TouchableOpacity style={styles.clearBtn} onPress={() => chat.clearMessages()}>
          <RefreshCw size={14} color="#f87171" />
        </TouchableOpacity>
      </View>

      {/* 5. Input Field Row */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder={`Tell ${activeAgent.name.split(" ")[0]} anything...`}
          placeholderTextColor="#6b7280"
          value={inputText}
          onChangeText={setInputText}
          multiline
          maxHeight={100}
        />
        {chat.isThinking ? (
          <View style={styles.thinkingContainer}>
            <ActivityIndicator color={activeAgent.color} size="small" />
          </View>
        ) : (
          <TouchableOpacity
            style={[styles.sendBtn, { backgroundColor: activeAgent.color }]}
            onPress={handleSend}
            disabled={!inputText.trim()}
          >
            <Send size={18} color="#000" />
          </TouchableOpacity>
        )}
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0e26",
  },
  agentSelectorWrapper: {
    borderBottomWidth: 1,
    borderBottomColor: "#1e1b4b",
    backgroundColor: "#11102e",
  },
  agentSelector: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 8,
  },
  agentBtn: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: "#1e1b4b",
    borderWidth: 1,
    borderColor: "#2e2b5c",
    gap: 6,
  },
  agentEmoji: {
    fontSize: 16,
  },
  agentName: {
    fontSize: 12,
    fontWeight: "700",
    color: "#9ca3af",
  },
  handoffContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#2e250c",
    borderBottomWidth: 1,
    borderBottomColor: "#fbbf24",
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  handoffText: {
    color: "#fef08a",
    fontSize: 11,
    lineHeight: 15,
  },
  handoffAcceptBtn: {
    backgroundColor: "#fbbf24",
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  handoffAcceptBtnText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#000",
  },
  messageList: {
    padding: 16,
    paddingBottom: 32,
    gap: 16,
  },
  welcomeContainer: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 40,
    paddingHorizontal: 20,
  },
  welcomeEmoji: {
    fontSize: 56,
    marginBottom: 16,
  },
  welcomeTitle: {
    fontSize: 22,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 8,
  },
  welcomeDescription: {
    fontSize: 14,
    color: "#9ca3af",
    textAlign: "center",
    lineHeight: 20,
    marginBottom: 24,
  },
  promptExamplesContainer: {
    width: "100%",
    gap: 8,
  },
  exampleBtn: {
    backgroundColor: "#1e1b4b",
    borderWidth: 1,
    borderColor: "#2e2b5c",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  exampleText: {
    color: "#a5b4fc",
    fontSize: 12,
    textAlign: "center",
    fontWeight: "600",
  },
  messageBubbleContainer: {
    flexDirection: "row",
    width: "100%",
  },
  userBubbleAlign: {
    justifyContent: "flex-end",
  },
  assistantBubbleAlign: {
    justifyContent: "flex-start",
  },
  messageBubble: {
    maxWidth: "85%",
    padding: 14,
    borderRadius: 20,
  },
  userBubble: {
    backgroundColor: "#4f46e5",
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: "#11102e",
    borderWidth: 1,
    borderBottomLeftRadius: 4,
  },
  userText: {
    color: "#fff",
    fontSize: 14,
    lineHeight: 20,
  },
  assistantText: {
    color: "#e2e8f0",
    fontSize: 14,
    lineHeight: 20,
  },
  bubbleActionRow: {
    flexDirection: "row",
    marginTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#1e1b4b",
    paddingTop: 8,
  },
  speakerBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  speakerText: {
    color: "#9ca3af",
    fontSize: 11,
    fontWeight: "600",
  },
  miniTasksContainer: {
    backgroundColor: "#080718",
    borderRadius: 12,
    padding: 10,
    marginTop: 10,
    gap: 6,
  },
  miniTaskRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  miniTaskEmoji: {
    fontSize: 13,
  },
  miniTaskText: {
    color: "#cbd5e1",
    fontSize: 12,
    fontWeight: "500",
  },
  moodSelectorContainer: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: "#1e1b4b",
    backgroundColor: "#11102e",
    gap: 8,
  },
  moodLabel: {
    fontSize: 11,
    color: "#6b7280",
    fontWeight: "700",
  },
  moodScroll: {
    gap: 6,
  },
  moodItem: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: "center",
    alignItems: "center",
  },
  clearBtn: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#2e1a1a",
    justifyContent: "center",
    alignItems: "center",
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#0f0e26",
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: "#11102e",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: "#fff",
    fontSize: 14,
    borderWidth: 1,
    borderColor: "#1e1b4b",
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: "center",
    alignItems: "center",
  },
  thinkingContainer: {
    width: 40,
    height: 40,
    justifyContent: "center",
    alignItems: "center",
  },
});
