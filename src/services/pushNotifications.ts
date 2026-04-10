import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { apiService } from './api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export async function registerForPushNotifications(): Promise<void> {
  if (!Device.isDevice) return; // simulators can't receive push

  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;

  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') return;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
    });
  }

  try {
    const { data: token } = await Notifications.getExpoPushTokenAsync();
    await apiService.registerDeviceToken(token);
  } catch {
    // silently fail — push is non-critical
  }
}

export function setupNotificationHandlers(
  onForeground: () => void,
  navigateToNotifications: () => void,
): () => void {
  const foregroundSub = Notifications.addNotificationReceivedListener(() => {
    onForeground();
  });

  const tapSub = Notifications.addNotificationResponseReceivedListener(() => {
    navigateToNotifications();
  });

  return () => {
    foregroundSub.remove();
    tapSub.remove();
  };
}
