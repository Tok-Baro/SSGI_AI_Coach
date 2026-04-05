import { initializeApp, getApps } from "firebase/app";
import { getMessaging, getToken, onMessage, type Messaging } from "firebase/messaging";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

let messaging: Messaging | null = null;

function getFirebaseMessaging(): Messaging | null {
  if (typeof window === "undefined") return null;
  if (!firebaseConfig.apiKey) return null;

  if (!messaging) {
    const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
    messaging = getMessaging(app);
  }
  return messaging;
}

export async function requestFCMToken(): Promise<string | null> {
  const m = getFirebaseMessaging();
  if (!m) return null;

  try {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") return null;

    const token = await getToken(m, {
      vapidKey: process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY,
    });
    return token;
  } catch (error) {
    console.error("FCM token request failed:", error);
    return null;
  }
}

export function onFCMMessage(callback: (payload: any) => void): void {
  const m = getFirebaseMessaging();
  if (!m) return;

  onMessage(m, (payload) => {
    callback(payload);
  });
}
