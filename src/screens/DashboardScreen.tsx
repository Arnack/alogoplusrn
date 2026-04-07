import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS, MAIN_MENU_ITEMS } from '../constants';
import { StatCard, Card } from '../components/Card';
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

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ navigation }) => {
  const [user, setUser] = useState<any>(null);
  const [rating, setRating] = useState<any>(null);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [userResponse, ratingResponse] = await Promise.all([
        apiService.getMe(),
        apiService.getRating(),
      ]);
      setUser(userResponse.data);
      setRating(ratingResponse.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const navigateToScreen = (screen: string) => {
    switch (screen) {
      case 'SearchOrders':
        navigation.navigate('SearchOrders');
        break;
      case 'MyOrders':
        navigation.navigate('MyOrders');
        break;
      case 'Wallet':
        navigation.navigate('Wallet');
        break;
      case 'Profile':
        navigation.navigate('Profile');
        break;
      case 'Notifications':
        navigation.navigate('Notifications');
        break;
      case 'Promotions':
        navigation.navigate('Promotions');
        break;
      default:
        break;
    }
  };

  if (loading) {
    return <LoadingScreen text="Загрузка..." />;
  }

  return (
    <SafeView style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Добро пожаловать</Text>
          <Text style={styles.userName}>
            {user?.lastName} {user?.firstName}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.profileButton}
          onPress={() => navigation.navigate('Profile')}
        >
          <Text style={styles.profileIcon}>👤</Text>
        </TouchableOpacity>
      </View>

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
        {/* Stats Cards */}
        <Card padding="medium" style={styles.statsCard}>
          <View style={styles.statsRow}>
            <StatCard
              label="Баланс"
              value={`${user?.balance || 0} ₽`}
              icon="💰"
              color={COLORS.success}
            />
            <StatCard
              label="Рейтинг"
              value={rating?.coefficient || 1.0}
              icon="⭐"
              color={COLORS.warning}
            />
          </View>
          <View style={styles.statsRow}>
            <StatCard
              label="Заказов"
              value={rating?.totalOrders || 0}
              icon="📋"
              color={COLORS.info}
            />
            <StatCard
              label="Выполнено"
              value={rating?.successfulOrders || 0}
              icon="✓"
              color={COLORS.success}
            />
          </View>
        </Card>

        {/* Main Menu Grid */}
        <View style={styles.menuGrid}>
          {MAIN_MENU_ITEMS.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={styles.menuItem}
              onPress={() => navigateToScreen(item.screen)}
            >
              <View style={[styles.menuIcon, { backgroundColor: item.color + '15' }]}>
                <Text style={styles.menuIconEmoji}>{item.icon}</Text>
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
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.l,
    paddingVertical: SPACING.m,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  greeting: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
  },
  userName: {
    fontSize: FONT_SIZES.xl,
    fontWeight: '700',
    color: COLORS.text,
  },
  profileButton: {
    width: 44,
    height: 44,
    borderRadius: BORDER_RADIUS.m,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileIcon: {
    fontSize: FONT_SIZES.xl,
  },
  scrollContent: {
    padding: SPACING.l,
  },
  statsCard: {
    marginBottom: SPACING.l,
  },
  statsRow: {
    flexDirection: 'row',
    gap: SPACING.m,
    marginBottom: SPACING.m,
  },
  menuGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.m,
    justifyContent: 'space-between',
  },
  menuItem: {
    width: '47%',
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.l,
    padding: SPACING.m,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  menuIcon: {
    width: 56,
    height: 56,
    borderRadius: BORDER_RADIUS.m,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.s,
  },
  menuIconEmoji: {
    fontSize: 28,
  },
  menuTitle: {
    fontSize: FONT_SIZES.s,
    color: COLORS.text,
    textAlign: 'center',
    fontWeight: '500',
  },
});
