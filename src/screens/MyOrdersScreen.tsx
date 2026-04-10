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
import { ConfirmationModal } from '../components/Modal';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Dashboard: undefined;
  MyOrders: undefined;
};

type MyOrdersScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'MyOrders'>;

interface MyOrdersScreenProps {
  navigation: MyOrdersScreenNavigationProp;
}

export const MyOrdersScreen: React.FC<MyOrdersScreenProps> = ({ navigation }) => {
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [withdrawingId, setWithdrawingId] = useState<number | null>(null);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    loadMyOrders();
  }, []);

  const loadMyOrders = async () => {
    setLoading(true);
    try {
      const data = await apiService.getMyOrders();
      const items: any[] = Array.isArray(data) ? data : (data as any)?.data || [];
      // Only show applications (not assigned orders)
      setApplications(items.filter((i: any) => i.kind === 'application'));
    } catch (err: any) {
      error('Ошибка загрузки заявок');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadMyOrders();
    setRefreshing(false);
  };

  const handleWithdrawApplication = async () => {
    if (!withdrawingId) return;

    try {
      await apiService.withdrawApplication(withdrawingId);
      success('Заявка отозвана');
      await loadMyOrders();
    } catch (err: any) {
      error(err.message);
    } finally {
      setWithdrawingId(null);
      setShowWithdrawModal(false);
    }
  };

  const getShiftLabel = (order: any) => {
    if (order.day_shift) return `День  ${order.day_shift}`;
    if (order.night_shift) return `Ночь  ${order.night_shift}`;
    return '—';
  };

  const getShiftColor = (order: any) => {
    return order.day_shift ? COLORS.day : COLORS.night;
  };

  const getDayOfWeekColor = () => {
    return COLORS.weekday;
  };

  const renderOrderCard = (order: any) => {
    // Determine status: if added_by_manager is true, it's approved, otherwise moderation
    const isApproved = order.added_by_manager === true;
    const statusLabel = isApproved ? 'Одобрен' : 'Модерация';
    const statusColor = isApproved ? COLORS.success : COLORS.warning;
    const statusBg = isApproved ? COLORS.success + '20' : COLORS.warning + '20';

    return (
      <Card key={order.order_id} style={styles.orderCard}>
        <View style={styles.orderHeader}>
          <View style={{ flex: 1, marginRight: SPACING.s }}>
            <Text style={styles.orderCustomer}>{order.organization || '—'}</Text>
            <Text style={styles.orderJob}>{order.job_name}</Text>
          </View>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: statusBg },
            ]}
          >
            <Text style={[styles.statusText, { color: statusColor }]}>
              {statusLabel}
            </Text>
          </View>
        </View>

        <View style={styles.orderDetails}>
          <View style={styles.orderDetail}>
            <Text style={styles.orderDetailLabel}>Дата</Text>
            <Text style={styles.orderDetailValue}>
              {order.date}
              {order.day_of_week ? (
                <Text style={{ color: getDayOfWeekColor(), fontWeight: '600' }}>{`, ${order.day_of_week}`}</Text>
              ) : null}
            </Text>
          </View>
          <View style={styles.orderDetail}>
            <Text style={styles.orderDetailLabel}>Смена</Text>
            <View style={[styles.shiftBadge, { backgroundColor: getShiftColor(order) + '20' }]}>
              <Text style={[styles.shiftBadgeText, { color: getShiftColor(order) }]}>
                {getShiftLabel(order)}
              </Text>
            </View>
          </View>
          <View style={styles.orderDetail}>
            <Text style={styles.orderDetailLabel}>Город</Text>
            <Text style={styles.orderDetailValue}>{order.city}</Text>
          </View>
          <View style={styles.orderDetail}>
            <Text style={styles.orderDetailLabel}>Оплата</Text>
            <Text style={[styles.orderDetailValue, styles.orderAmount]}>
              {order.amount_adjusted || '—'} ₽
            </Text>
          </View>
        </View>

        <Button
          title="Отозвать заявку"
          onPress={() => {
            setWithdrawingId(order.order_id);
            setShowWithdrawModal(true);
          }}
          variant="outline"
          fullWidth
        />
      </Card>
    );
  };

  if (loading) {
    return <LoadingScreen text="Загрузка заявок..." />;
  }

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Управление заявками" onBack={() => navigation.goBack()} />

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
        {applications.length === 0 ? (
          <Card>
            <Text style={styles.emptyText}>Нет заявок</Text>
          </Card>
        ) : (
          applications.map((app) => renderOrderCard(app))
        )}
      </ScrollView>

      {/* Withdraw Confirmation Modal */}
      <ConfirmationModal
        visible={showWithdrawModal}
        title="Отозвать заявку"
        message="Вы уверены, что хотите отозвать заявку? Это может повлиять на ваш рейтинг."
        confirmText="Отозвать"
        cancelText="Отмена"
        onConfirm={handleWithdrawApplication}
        onCancel={() => setShowWithdrawModal(false)}
        variant="danger"
      />

      <ToastContainer />
    </SafeView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
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
  orderCard: {
    marginBottom: SPACING.m,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.m,
  },
  orderCustomer: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
  },
  orderJob: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
  statusBadge: {
    paddingHorizontal: SPACING.m,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.round,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statusText: {
    fontSize: FONT_SIZES.s,
    fontWeight: '600',
    textAlignVertical: 'center',
  },
  orderDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.m,
    marginBottom: SPACING.m,
  },
  orderDetail: {
    flex: 1,
    minWidth: '45%',
  },
  orderDetailLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    marginBottom: SPACING.xs,
  },
  orderDetailValue: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    fontWeight: '500',
  },
  orderAmount: {
    color: COLORS.success,
    fontWeight: '700',
  },
  shiftBadge: {
    paddingHorizontal: SPACING.s,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.s,
    alignSelf: 'flex-start',
  },
  shiftBadgeText: {
    fontSize: FONT_SIZES.s,
    fontWeight: '600',
  },
});
