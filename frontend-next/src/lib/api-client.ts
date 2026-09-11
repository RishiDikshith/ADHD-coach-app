"use client";

// Re-export from the consolidated API service for backward compatibility.
// All API logic lives in @/services/api.ts
export {
  api,
  ApiError,
  type TrustedDeviceItem,
  type ConnectedAccountItem,
  type UserTicket,
} from "@/services/api";
