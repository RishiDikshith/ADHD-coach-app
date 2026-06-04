import { WS_URL } from "@/lib/api";
// Dynamically switch to wss:// if site is loaded over https://
const getWsBase = () => {
  if (typeof window !== "undefined") {
    const isHttps = window.location.protocol === "https:";
    if (isHttps && WS_URL.startsWith("ws://")) {
      return WS_URL.replace("ws://", "wss://");
    }
  }
  return WS_URL;
};
const WS_BASE = getWsBase();

export type WebSocketConnectionState = "CONNECTING" | "OPEN" | "CLOSING" | "CLOSED";

export interface FocusTimerState {
  duration_minutes: number;
  remaining_seconds: number;
  is_active: boolean;
  is_break: boolean;
}

export interface FocusRoomMember {
  username: string;
  status: "idle" | "focusing" | "break" | "paused";
  distractions: number;
  avatar_hsl: string;
  joined_at: string;
}

export interface FocusRoomState {
  room_id: string;
  timer: FocusTimerState;
  members: FocusRoomMember[];
}

export interface AccountabilityGroupMember {
  username: string;
  status: string;
  stress: number;
  energy: number;
  dopamine_points: number;
  avatar_hsl: string;
}

export interface AccountabilityCheckIn {
  username: string;
  status: string;
  stress: number;
  energy: number;
  timestamp: string;
}

export interface AccountabilityMicroWin {
  username: string;
  task: string;
  timestamp: string;
}

export interface DopamineAward {
  from_username: string;
  to_username: string;
  emoji: string;
  points: number;
  target_total_points: number;
}

// Custom WebSocket manager with heartbeats and automatic recovery
class BaseWebSocketClient {
  protected ws: WebSocket | null = null;
  protected url: string;
  protected stateCallback: (state: WebSocketConnectionState) => void;
  protected reconnectAttempts = 0;
  protected maxReconnectAttempts = 5;
  protected reconnectDelay = 1000;
  protected pingInterval: any = null;
  protected reconnectTimeout: any = null;
  protected shouldReconnect = true;

  constructor(url: string, onStateChange: (state: WebSocketConnectionState) => void) {
    this.url = url;
    this.stateCallback = onStateChange;
  }

  public connect() {
    this.shouldReconnect = true;
    this.stateCallback("CONNECTING");

    // Clean up any existing connection and heartbeat before starting a new one
    this.stopHeartbeat();
    if (this.ws) {
      try {
        this.ws.onopen = null;
        this.ws.onmessage = null;
        this.ws.onerror = null;
        this.ws.onclose = null;
        this.ws.close();
      } catch (e) {
        console.warn("Error closing old WebSocket:", e);
      }
      this.ws = null;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.stateCallback("OPEN");
        this.startHeartbeat();
        this.onConnected();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onMessageReceived(data);
        } catch (e) {
          console.warn("WS received non-JSON or invalid payload:", event.data);
        }
      };

      this.ws.onerror = (err) => {
        console.error("WS error encountered:", err);
      };

      this.ws.onclose = () => {
        this.stateCallback("CLOSED");
        this.stopHeartbeat();
        if (this.shouldReconnect) {
          this.attemptReconnect();
        }
      };
    } catch (err) {
      console.error("Failed to connect WS:", err);
      this.stateCallback("CLOSED");
      this.attemptReconnect();
    }
  }

  public disconnect() {
    this.shouldReconnect = false;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      try {
        this.ws.onopen = null;
        this.ws.onmessage = null;
        this.ws.onerror = null;
        this.ws.onclose = null;
        this.ws.close();
      } catch (e) {}
      this.ws = null;
    }
    this.stateCallback("CLOSED");
  }

  protected send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn("Attempted to send message over closed WebSocket connection:", message);
    }
  }

  protected onConnected() {}
  protected onMessageReceived(data: any) {}

  private startHeartbeat() {
    this.pingInterval = setInterval(() => {
      this.send({ type: "ping" });
    }, 25000); // 25 seconds heartbeat
  }

  private stopHeartbeat() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("WebSocket reached max reconnection attempts");
      return;
    }
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.reconnectAttempts++;
    const delay = Math.min(30000, this.reconnectDelay * Math.pow(2, this.reconnectAttempts)) + Math.random() * 1000;
    console.log(`Reconnecting to WebSocket in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts})...`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      if (this.shouldReconnect) {
        this.connect();
      }
    }, delay);
  }
}

// ==========================================
// 1. LIVE CO-WORKING FOCUS ROOM CLIENT
// ==========================================

export class FocusRoomWebSocketClient extends BaseWebSocketClient {
  private onRoomUpdate: (roomState: FocusRoomState) => void;
  private onTimerTick: (timer: FocusTimerState) => void;
  private onTimerCompleted: (isBreak: boolean) => void;
  private onDistractionLogged: (info: { username: string; category: string; total: number }) => void;
  private onNotification: (msg: string) => void;

  constructor(
    room_id: string,
    username: string,
    onStateChange: (state: WebSocketConnectionState) => void,
    callbacks: {
      onRoomUpdate: (roomState: FocusRoomState) => void;
      onTimerTick: (timer: FocusTimerState) => void;
      onTimerCompleted: (isBreak: boolean) => void;
      onDistractionLogged: (info: { username: string; category: string; total: number }) => void;
      onNotification: (msg: string) => void;
    }
  ) {
    const encodedUser = encodeURIComponent(username);
    super(`${WS_BASE}/focus/${room_id}?username=${encodedUser}`, onStateChange);
    this.onRoomUpdate = callbacks.onRoomUpdate;
    this.onTimerTick = callbacks.onTimerTick;
    this.onTimerCompleted = callbacks.onTimerCompleted;
    this.onDistractionLogged = callbacks.onDistractionLogged;
    this.onNotification = callbacks.onNotification;
  }

  // --- Send actions ---

  public updateStatus(status: "idle" | "focusing" | "break" | "paused") {
    this.send({ type: "update_status", status });
  }

  public logDistraction(category: string) {
    this.send({ type: "log_distraction", category });
  }

  public startTimer(durationMinutes: number, isBreak = false) {
    this.send({ type: "start_timer", duration_minutes: durationMinutes, is_break: isBreak });
  }

  public pauseTimer() {
    this.send({ type: "pause_timer" });
  }

  public resumeTimer() {
    this.send({ type: "resume_timer" });
  }

  public resetTimer() {
    this.send({ type: "reset_timer" });
  }

  // --- Receive handlers ---

  protected onMessageReceived(data: any) {
    switch (data.type) {
      case "member_joined":
        this.onNotification(`👋 ${data.username} joined the co-working room!`);
        this.onRoomUpdate({
          room_id: "", // filled by context
          timer: data.timer,
          members: data.members
        });
        break;
      
      case "member_left":
        this.onNotification(`🚪 ${data.username} left the room`);
        this.onRoomUpdate({
          room_id: "",
          timer: { duration_minutes: 25, remaining_seconds: 1500, is_active: false, is_break: false },
          members: data.members
        });
        break;

      case "status_changed":
        const emoji = data.status === "focusing" ? "🎯" : data.status === "break" ? "☕" : "⏸️";
        this.onNotification(`✨ ${data.username} is now ${data.status} ${emoji}`);
        break;

      case "distraction_logged":
        this.onDistractionLogged({
          username: data.username,
          category: data.category,
          total: data.total_distractions
        });
        break;

      case "timer_started":
        this.onTimerTick(data.timer);
        this.onNotification(`🎯 Focus session synchronized and started!`);
        break;

      case "timer_paused":
        this.onTimerTick(data.timer);
        this.onNotification(`⏸️ Session paused by teammates.`);
        break;

      case "timer_resumed":
        this.onTimerTick(data.timer);
        this.onNotification(`▶️ Focus timer resumed.`);
        break;

      case "timer_reset":
        this.onTimerTick(data.timer);
        this.onNotification(`🔄 Timer reset to initial state.`);
        break;

      case "timer_tick":
        this.onTimerTick({
          duration_minutes: 25, // placeholder
          remaining_seconds: data.remaining_seconds,
          is_active: data.is_active,
          is_break: data.is_break
        });
        break;

      case "timer_completed":
        this.onTimerCompleted(data.is_break);
        this.onNotification(data.is_break ? "☕ Break finished! Time to flow again." : "🎉 Congratulations! Focus block completed successfully! +25XP");
        break;

      case "pong":
        // Hearthbeat confirmed
        break;
    }
  }
}

// ==========================================
// 2. COLLABORATIVE ACCOUNTABILITY CLIENT
// ==========================================

export class AccountabilityWebSocketClient extends BaseWebSocketClient {
  private onPresenceUpdate: (members: AccountabilityGroupMember[]) => void;
  private onCheckIn: (checkIn: AccountabilityCheckIn) => void;
  private onMicroWin: (microWin: AccountabilityMicroWin) => void;
  private onDopamineReceived: (award: DopamineAward) => void;

  constructor(
    group_id: string,
    username: string,
    onStateChange: (state: WebSocketConnectionState) => void,
    callbacks: {
      onPresenceUpdate: (members: AccountabilityGroupMember[]) => void;
      onCheckIn: (checkIn: AccountabilityCheckIn) => void;
      onMicroWin: (microWin: AccountabilityMicroWin) => void;
      onDopamineReceived: (award: DopamineAward) => void;
    }
  ) {
    const encodedUser = encodeURIComponent(username);
    super(`${WS_BASE}/accountability/${group_id}?username=${encodedUser}`, onStateChange);
    this.onPresenceUpdate = callbacks.onPresenceUpdate;
    this.onCheckIn = callbacks.onCheckIn;
    this.onMicroWin = callbacks.onMicroWin;
    this.onDopamineReceived = callbacks.onDopamineReceived;
  }

  // --- Send actions ---

  public checkIn(status: string, stress: number, energy: number) {
    this.send({ type: "check_in", status, stress, energy });
  }

  public completeMicroWin(task: string) {
    this.send({ type: "micro_win", task });
  }

  public sendDopamine(targetUsername: string, emoji = "🎉") {
    this.send({ type: "send_dopamine", target_username: targetUsername, emoji });
  }

  // --- Receive handlers ---

  protected onMessageReceived(data: any) {
    switch (data.type) {
      case "presence_update":
        this.onPresenceUpdate(data.members);
        break;

      case "member_check_in":
        this.onCheckIn({
          username: data.username,
          status: data.status,
          stress: data.stress,
          energy: data.energy,
          timestamp: data.timestamp
        });
        break;

      case "member_micro_win":
        this.onMicroWin({
          username: data.username,
          task: data.task,
          timestamp: data.timestamp
        });
        break;

      case "dopamine_received":
        this.onDopamineReceived({
          from_username: data.from_username,
          to_username: data.to_username,
          emoji: data.emoji,
          points: data.points,
          target_total_points: data.target_total_points
        });
        break;
    }
  }
}

// ==========================================
// 3. LOW-LATENCY STREAMING AI CHAT CLIENT
// ==========================================

export class StreamingChatWebSocketClient extends BaseWebSocketClient {
  private onToken: (token: string) => void;
  private onStreamStart: () => void;
  private onStreamEnd: () => void;
  private onMetadata: (payload: any) => void;
  private onError: (err: string) => void;

  constructor(
    username: string,
    agent_id: string,
    onStateChange: (state: WebSocketConnectionState) => void,
    callbacks: {
      onToken: (token: string) => void;
      onStreamStart: () => void;
      onStreamEnd: () => void;
      onMetadata: (payload: any) => void;
      onError: (err: string) => void;
    }
  ) {
    const encodedUser = encodeURIComponent(username);
    const encodedAgent = encodeURIComponent(agent_id);
    super(`${WS_BASE}/chat?username=${encodedUser}&agent_id=${encodedAgent}`, onStateChange);
    this.onToken = callbacks.onToken;
    this.onStreamStart = callbacks.onStreamStart;
    this.onStreamEnd = callbacks.onStreamEnd;
    this.onMetadata = callbacks.onMetadata;
    this.onError = callbacks.onError;
  }

  // --- Send actions ---

  public sendMessage(
    text: string,
    userData: Record<string, any> = {},
    sessionData: Record<string, any> = {},
    history: any[] = [],
    language = "en",
    languageName = "English"
  ) {
    this.send({
      text,
      user_data: userData,
      session_data: sessionData,
      history,
      language,
      language_name: languageName
    });
  }

  // --- Receive handlers ---

  protected onMessageReceived(data: any) {
    switch (data.type) {
      case "stream_start":
        this.onStreamStart();
        break;

      case "token":
        this.onToken(data.token);
        break;

      case "stream_end":
        this.onStreamEnd();
        break;

      case "metadata":
        this.onMetadata(data.metadata);
        break;

      case "error":
        this.onError(data.message);
        break;
    }
  }
}
