import React from "react";
import { StyleSheet, View } from "react-native";
import { ChatInterface } from "../../src/components/ChatInterface";

export default function ChatScreen() {
  return (
    <View style={styles.container}>
      <ChatInterface />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f0e26",
  },
});
