import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { LoadingScreen } from '../components/Loading';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Dashboard: undefined;
  Notifications: undefined;
};

type NotificationsScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Notifications'>;

interface NotificationsScreenProps {
  navigation: NotificationsScreenNavigationProp;
}

export const NotificationsScreen: React.FC<NotificationsScreenProps> = ({ navigation }) => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [markingRead, setMarkingRead] = useState(false);
  const { error, ToastContainer } = useToast();

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const response = await apiService.getNotifications();
      setNotifications(response.data ?? []);
    } catch (err: any) {
      error('Ошибка загрузки уведомлений');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadNotifications();
    setRefreshing(false);
  };

  const markAllRead = async () => {
    const unreadIds = notifications.filter((n) => !n.isRead).map((n) => n.id);
    
    if (unreadIds.length === 0) {
      return;
    }

    setMarkingRead(true);
    try {
      await apiService.markNotificationsAsRead(unreadIds);
      setNotifications(
        notifications.map((n) => ({ ...n, isRead: true }))
      );
    } catch (err: any) {
      error('Ошибка при отметке прочитанных');
    } finally {
      setMarkingRead(false);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'order':
        return '📋';
      case 'payment':
        return '💰';
      case 'promotion':
        return '🎁';
      default:
        return '📢';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'order':
        return COLORS.info;
      case 'payment':
        return COLORS.success;
      case 'promotion':
        return COLORS.warning;
      default:
        return COLORS.gray;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) {
      return 'Только что';
    } else if (hours < 24) {
      return `${hours} ч. назад`;
    } else if (days < 7) {
      return `${days} дн. назад`;
    } else {
      return date.toLocaleDateString('ru-RU');
    }
  };

  if (loading) {
    return <LoadingScreen text="Загрузка уведомлений..." />;
  }

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <SafeView style={styles.container}>
      <ScreenHeader
        title="Уведомления"
        onBack={() => navigation.goBack()}
        right={unreadCount > 0 ? (
          <Button
            title="Прочитать все"
            onPress={markAllRead}
            loading={markingRead}
            variant="outline"
            size="small"
          />
        ) : undefined}
      />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[COLORS.primary]}
            tintColor={COLORS.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {notifications.length === 0 ? (
          <Card>
            <Text style={styles.emptyText}>Нет уведомлений</Text>
          </Card>
        ) : (
          notifications.map((notification) => (
            <Card
              key={notification.id}
              style={[
                styles.notificationCard,
                !notification.isRead && styles.notificationCardUnread,
              ] as any}
            >
              <View style={styles.notificationContent}>
                <View
                  style={[
                    styles.notificationIcon,
                    {
                      backgroundColor:
                        getNotificationColor(notification.type) + '20',
                    },
                  ]}
                >
                  <Text style={styles.notificationIconEmoji}>
                    {getNotificationIcon(notification.type)}
                  </Text>
                </View>
                <View style={styles.notificationText}>
                  <Text style={styles.notificationTitle}>
                    {notification.title}
                  </Text>
                  <Text style={styles.notificationMessage}>
                    {notification.message}
                  </Text>
                  <Text style={styles.notificationDate}>
                    {formatDate(notification.createdAt)}
                  </Text>
                </View>
                {!notification.isRead && <View style={styles.unreadDot} />}
              </View>
            </Card>
          ))
        )}
      </ScrollView>
      <ToastContainer />
    </SafeView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  unreadCount: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
  },
  scrollContent: {
    padding: SPACING.l,
  },
  emptyText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
    textAlign: 'center',
    padding: SPACING.xl,
  },
  notificationCard: {
    marginBottom: SPACING.m,
  },
  notificationCardUnread: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
  },
  notificationContent: {
    flexDirection: 'row',
  },
  notificationIcon: {
    width: 48,
    height: 48,
    borderRadius: BORDER_RADIUS.m,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  notificationIconEmoji: {
    fontSize: 24,
  },
  notificationText: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: FONT_SIZES.m,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  notificationMessage: {
    fontSize: FONT_SIZES.s,
    color: COLORS.text,
    marginBottom: SPACING.xs,
    lineHeight: 20,
  },
  notificationDate: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.primary,
    marginTop: 8,
    marginLeft: SPACING.s,
  },
});
