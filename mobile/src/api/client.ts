import axios from "axios";
import { Platform } from "react-native";

const API_TIMEOUT = 30000;

// Auto-detect IP for emulators vs real devices (change with production endpoint as needed)
export const API_BASE = Platform.select({
  android: "http://10.0.2.2:8000", // Android emulator maps localhost to 10.0.2.2
  ios: "http://localhost:8000",     // iOS simulator maps to localhost
  default: "http://localhost:8000",
});

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

let cachedToken: string | null = null;

// Synchronously inject auth token from Zustand/MMKV storage
export const setAuthToken = (token: string | null) => {
  cachedToken = token;
};

// Request interceptor to automatically inject authorization token
apiClient.interceptors.request.use(
  async (config) => {
    if (cachedToken) {
      config.headers.Authorization = `Bearer ${cachedToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle unified error mappings
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response ? error.response.status : 0;
    const data = error.response ? error.response.data : null;
    let message = "A connection error occurred. Please check your network.";

    if (data && typeof data === "object") {
      message = data.detail || data.message || error.message || message;
    } else if (error.message) {
      message = error.message;
    }

    const appError = new Error(message) as any;
    appError.status = status;
    appError.data = data;
    appError.originalError = error;

    return Promise.reject(appError);
  }
);

export default apiClient;
