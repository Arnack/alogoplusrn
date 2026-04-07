import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { LoadingScreen } from '../components/Loading';
import { SafeView } from '../components/SafeView';
import { apiService } from '../services/api';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Dashboard: undefined;
  SearchOrders: undefined;
  MyOrders: undefined;
  Wallet: undefined;
  Profile: undefined;
  Notifications: undefined;
  Promotions: undefined;
  OrderDetails: { orderId: number };
};

type DashboardScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Dashboard'>;

interface DashboardScreenProps {
  navigation: DashboardScreenNavigationProp;
}

const MENU_ITEMS = [
  {
    id: 'search_orders',
    title: 'Поиск заказов',
    icon: 'search-outline' as const,
    screen: 'SearchOrders',
    color: '#4A90D9',
    bg: '#EBF4FF',
  },
  {
    id: 'my_orders',
    title: 'Мои заказы',
    icon: 'document-text-outline' as const,
    screen: 'MyOrders',
    color: '#7B68EE',
    bg: '#F0EEFF',
  },
  {
    id: 'wallet',
    title: 'Кошелёк',
    icon: 'wallet-outline' as const,
    screen: 'Wallet',
    color: '#27AE60',
    bg: '#EAFAF1',
  },
  {
    id: 'profile',
    title: 'Профиль',
    icon: 'person-outline' as const,
    screen: 'Profile',
    color: '#E67E22',
    bg: '#FEF5E7',
  },
  {
    id: 'notifications',
    title: 'Уведомления',
    icon: 'notifications-outline' as const,
    screen: 'Notifications',
    color: '#E74C3C',
    bg: '#FDEDEC',
  },
  {
    id: 'promotions',
    title: 'Акции',
    icon: 'gift-outline' as const,
    screen: 'Promotions',
    color: '#16A085',
    bg: '#E8F8F5',
  },
];

const STATS = (user: any, rating: any) => [
  { label: 'Баланс', value: `${user?.balance || 0} ₽`, icon: 'cash-outline' as const, color: '#27AE60', bg: '#EAFAF1' },
  { label: 'Рейтинг', value: `${rating?.coefficient ?? 1.0}`, icon: 'star-outline' as const, color: '#F39C12', bg: '#FEF9E7' },
  { label: 'Заказов', value: `${rating?.totalOrders ?? 0}`, icon: 'briefcase-outline' as const, color: '#4A90D9', bg: '#EBF4FF' },
  { label: 'Выполнено', value: `${rating?.successfulOrders ?? 0}`, icon: 'checkmark-circle-outline' as const, color: '#7B68EE', bg: '#F0EEFF' },
];

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ navigation }) => {
  const [user, setUser] = useState<any>(null);
  const [rating, setRating] = useState<any>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [userRes, ratingRes, notifRes] = await Promise.all([
        apiService.getMe(),
        apiService.getRating(),
        apiService.getNotifications(),
      ]);
      setUser(userRes.data);
      setRating(ratingRes.data);
      setUnreadCount((notifRes.data || []).filter((n: any) => !n.isRead).length);
    } catch (e) {
      console.error('Dashboard load error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  if (loading) return <LoadingScreen text="Загрузка..." />;

  const initials = `${(user?.lastName || '')[0] ?? ''}${(user?.firstName || '')[0] ?? ''}`.toUpperCase() || '?';
  const stats = STATS(user, rating);

  return (
    <SafeView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.avatarWrap} onPress={() => navigation.navigate('Profile')} activeOpacity={0.8}>
          <Text style={styles.avatarText}>{initials}</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.greeting}>Добро пожаловать</Text>
          <Text style={styles.userName} numberOfLines={1}>{user?.lastName} {user?.firstName}</Text>
        </View>
        <TouchableOpacity style={styles.bellWrap} onPress={() => navigation.navigate('Notifications')} activeOpacity={0.8}>
          <Ionicons name="notifications-outline" size={24} color={COLORS.text} />
          {unreadCount > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{unreadCount > 99 ? '99+' : unreadCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} tintColor={COLORS.primary} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Stats */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.statsRow}>
          {stats.map((s) => (
            <View key={s.label} style={styles.statCard}>
              <View style={[styles.statIconWrap, { backgroundColor: s.bg }]}>
                <Ionicons name={s.icon} size={22} color={s.color} />
              </View>
              <Text style={styles.statValue}>{s.value}</Text>
              <Text style={styles.statLabel}>{s.label}</Text>
            </View>
          ))}
        </ScrollView>

        {/* Menu */}
        <Text style={styles.sectionTitle}>Меню</Text>
        <View style={styles.menuGrid}>
          {MENU_ITEMS.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={styles.menuCard}
              onPress={() => navigation.navigate(item.screen as any)}
              activeOpacity={0.75}
            >
              <View style={[styles.menuIconWrap, { backgroundColor: item.bg }]}>
                <Ionicons name={item.icon} size={26} color={item.color} />
              </View>
              <Text style={styles.menuTitle}>{item.title}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F4F6FA',
  },

  /* Header */
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.l,
    paddingVertical: SPACING.m,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: '#EAECF0',
  },
  avatarWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  avatarText: {
    fontSize: FONT_SIZES.m,
    fontWeight: '700',
    color: COLORS.white,
  },
  headerCenter: {
    flex: 1,
  },
  greeting: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    marginBottom: 1,
  },
  userName: {
    fontSize: FONT_SIZES.m,
    fontWeight: '700',
    color: COLORS.text,
  },
  bellWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#F4F6FA',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badge: {
    position: 'absolute',
    top: 6,
    right: 6,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: COLORS.error,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 3,
    borderWidth: 1.5,
    borderColor: COLORS.white,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '800',
    color: COLORS.white,
  },

  /* Scroll */
  scroll: {
    paddingBottom: SPACING.xl,
  },

  /* Stats */
  statsRow: {
    paddingHorizontal: SPACING.l,
    paddingTop: SPACING.l,
    paddingBottom: SPACING.s,
    gap: SPACING.m,
  },
  statCard: {
    width: 96,
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    paddingVertical: SPACING.m,
    paddingHorizontal: SPACING.s,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statIconWrap: {
    width: 44,
    height: 44,
    borderRadius: BORDER_RADIUS.m,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.s,
  },
  statValue: {
    fontSize: FONT_SIZES.m,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 2,
  },
  statLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    textAlign: 'center',
  },

  /* Menu */
  sectionTitle: {
    fontSize: FONT_SIZES.s,
    fontWeight: '600',
    color: COLORS.gray,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    paddingHorizontal: SPACING.l,
    paddingTop: SPACING.m,
    paddingBottom: SPACING.s,
  },
  menuGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: SPACING.l,
    gap: SPACING.m,
  },
  menuCard: {
    width: '47%',
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    paddingVertical: SPACING.l,
    paddingHorizontal: SPACING.m,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  menuIconWrap: {
    width: 58,
    height: 58,
    borderRadius: BORDER_RADIUS.l,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.s,
  },
  menuTitle: {
    fontSize: FONT_SIZES.s,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
  },
});
