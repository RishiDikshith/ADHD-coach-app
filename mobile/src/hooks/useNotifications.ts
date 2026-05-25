import { useEffect, useRef, useState } from "react";
import { Platform } from "react-native";
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";

// Configure default notification presentation style
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export const useNotifications = () => {
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
  const [notification, setNotification] = useState<Notifications.Notification | null>(null);
  const notificationListener = useRef<any>();
  const responseListener = useRef<any>();

  useEffect(() => {
    registerForPushNotificationsAsync().then((token) => {
      if (token) setExpoPushToken(token);
    });

    // Listen for incoming notifications when the app is active
    notificationListener.current = Notifications.addNotificationReceivedListener((notif) => {
      setNotification(notif);
    });

    // Listen for when a user clicks/taps on a notification
    responseListener.current = Notifications.addNotificationResponseReceivedListener((response) => {
      console.log("Notification tapped:", response.notification.request.content.data);
    });

    return () => {
      if (notificationListener.current) {
        Notifications.removeNotificationSubscription(notificationListener.current);
      }
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
      }
    };
  }, []);

  // Schedule a local alarm (e.g., Pomodoro complete)
  const scheduleLocalNotification = async (
    title: string,
    body: string,
    secondsDelay: number,
    data: Record<string, any> = {}
  ) => {
    try {
      const identifier = await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          data,
          sound: Platform.OS === "ios" ? true : undefined,
        },
        trigger: {
          seconds: secondsDelay,
        },
      });
      return identifier;
    } catch (e) {
      console.error("Failed to schedule notification:", e);
      return null;
    }
  };

  // Schedule a recurring reminder (e.g. daily accountability check-in)
  const scheduleDailyAccountabilityCheckIn = async (hour: number, minute: number) => {
    try {
      // Clear previous check-ins to prevent duplicates
      await cancelAllScheduledNotifications();

      const identifier = await Notifications.scheduleNotificationAsync({
        content: {
          title: "🤝 High-Energy Check-in Time!",
          body: "Let's capture our small wins and log our energy levels. You're doing great!",
          data: { screen: "dashboard" },
        },
        trigger: {
          hour,
          minute,
          repeats: true,
        },
      });
      return identifier;
    } catch (e) {
      console.error("Failed to schedule daily check-in:", e);
      return null;
    }
  };

  const cancelNotification = async (id: string) => {
    await Notifications.cancelScheduledNotificationAsync(id);
  };

  const cancelAllScheduledNotifications = async () => {
    await Notifications.cancelAllScheduledNotificationsAsync();
  };

  return {
    expoPushToken,
    notification,
    scheduleLocalNotification,
    scheduleDailyAccountabilityCheckIn,
    cancelNotification,
    cancelAllScheduledNotifications,
  };
};

// Request permissions & set up android channel
async function registerForPushNotificationsAsync() {
  let token: string | null = null;

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "default",
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#FF231F7C",
    });
    
    // Add special focus alarm channel
    await Notifications.setNotificationChannelAsync("focus-alarms", {
      name: "Focus Alarms",
      importance: Notifications.AndroidImportance.HIGH,
      enableVibrate: true,
      lightColor: "#6ee7b7",
    });
  }

  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== "granted") {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== "granted") {
      console.log("Failed to get push token for push notification!");
      return null;
    }

    try {
      // expoProjectID is auto-resolved in newer Expo versions, otherwise fetched from app.json credentials
      const tokenData = await Notifications.getExpoPushTokenAsync();
      token = tokenData.data;
    } catch (err) {
      console.log("Error getting Expo Push Token:", err);
    }
  } else {
    console.log("Must use physical device for Push Notifications (Simulator detected).");
  }

  return token;
}
