import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
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
    const projectId =
      Constants?.expoConfig?.extra?.eas?.projectId ?? Constants?.easConfig?.projectId;
    if (!projectId) {
      console.warn('Project ID not found in Constants. Push notifications may not work.');
    }
    const { data: token } = await Notifications.getExpoPushTokenAsync({
      projectId,
    });
    await apiService.registerDeviceToken(token);
  } catch (error) {
    console.error('Error getting expo push token', error);
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
