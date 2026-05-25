import { StateStorage } from "zustand/middleware";

let mmkv: any = null;

try {
  // react-native-mmkv is native code. In Expo Go (without custom dev client),
  // requiring it might fail. We use a dynamic try-catch wrapper for bulletproof fallback.
  const { MMKV } = require("react-native-mmkv");
  mmkv = new MMKV({ id: "adhd-coach-persistent-storage" });
  console.log("[StorageAdapter] Secure MMKV initialized successfully.");
} catch (e) {
  console.log(
    "[StorageAdapter] MMKV native module not found (normal in standard Expo Go)." +
    " Falling back to AsyncStorage."
  );
}

// Lazy load AsyncStorage
const getAsyncStorage = () => {
  return require("@react-native-async-storage/async-storage").default;
};

export const hybridStorage: StateStorage = {
  setItem: async (name, value) => {
    if (mmkv) {
      mmkv.set(name, value);
      return;
    }
    await getAsyncStorage().setItem(name, value);
  },
  getItem: async (name) => {
    if (mmkv) {
      return mmkv.getString(name) ?? null;
    }
    return await getAsyncStorage().getItem(name);
  },
  removeItem: async (name) => {
    if (mmkv) {
      mmkv.delete(name);
      return;
    }
    await getAsyncStorage().removeItem(name);
  },
};

export default hybridStorage;
