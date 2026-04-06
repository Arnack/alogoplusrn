import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS, SHIFT_TIMES } from '../constants';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { LoadingScreen } from '../components/Loading';
import { ConfirmationModal } from '../components/Modal';
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
  const [assignedOrders, setAssignedOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'applications' | 'assigned'>('applications');
  const [withdrawingId, setWithdrawingId] = useState<number | null>(null);
  const [refusingId, setRefusingId] = useState<number | null>(null);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [showRefuseModal, setShowRefuseModal] = useState(false);
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    loadMyOrders();
  }, []);

  const loadMyOrders = async () => {
    setLoading(true);
    try {
      const response = await apiService.getMyOrders();
      setApplications(response.data.applications || []);
      setAssignedOrders(response.data.assigned || []);
    } catch (err: any) {
      error('Ошибка загрузки заказов');
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

  const handleRefuseAssignment = async () => {
    if (!refusingId) return;
    
    try {
      await apiService.refuseAssignment(refusingId);
      success('Отказ от заказа');
      await loadMyOrders();
    } catch (err: any) {
      error(err.message);
    } finally {
      setRefusingId(null);
      setShowRefuseModal(false);
    }
  };

  const getShiftColor = (shift: string) => {
    return shift === 'day' ? COLORS.day : COLORS.night;
  };

  const renderOrderCard = (order: any, isApplication: boolean) => {
    return (
      <Card key={order.id} style={styles.orderCard}>
        <View style={styles.orderHeader}>
          <View>
            <Text style={styles.orderCustomer}>{order.customerName}</Text>
            <Text style={styles.orderJob}>{order.jobName}</Text>
          </View>
          <View
            style={[
              styles.statusBadge,
              {
                backgroundColor: isApplication ? COLORS.info + '20' : COLORS.success + '20',
              },
            ]}
          >
            <Text
              style={[
                styles.statusText,
                {
                  color: isApplication ? COLORS.info : COLORS.success,
                },
              ]}
            >
              {isApplication ? 'Заявка' : 'Назначен'}
            </Text>
          </View>
        </View>

        <View style={styles.orderDetails}>
          <View style={styles.orderDetail}>
            <Text style={styles.orderDetailLabel}>Дата</Text>
            <Text style={styles.orderDetailValue}>{order.date}</Text>
          </View>
          <View style={styles.orderDetail}>
            <Text style={styles.orderDetailLabel}>Смена</Text>
            <View
              style={[
                styles.shiftBadge,
                { backgroundColor: getShiftColor(order.shift) + '20' },
              ]}
            >
              <Text
                style={[styles.shiftBadgeText, { color: getShiftColor(order.shift) }]}
              >
                {order.shift === 'day' ? 'День' : 'Ночь'}
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
              {order.adjustedAmount || order.amount} ₽
            </Text>
          </View>
        </View>

        {isApplication && (
          <Button
            title="Отозвать заявку"
            onPress={() => {
              setWithdrawingId(order.id);
              setShowWithdrawModal(true);
            }}
            variant="outline"
            fullWidth
          />
        )}

        {!isApplication && (
          <View style={styles.assignedActions}>
            <Button
              title="Отказаться"
              onPress={() => {
                setRefusingId(order.id);
                setShowRefuseModal(true);
              }}
              variant="outline"
              style={styles.assignedAction}
            />
            <Button
              title="Подписать акт"
              onPress={() => success('Функция подписания акта')}
              variant="primary"
              style={styles.assignedAction}
            />
          </View>
        )}
      </Card>
    );
  };

  if (loading) {
    return <LoadingScreen text="Загрузка заказов..." />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Мои заказы</Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'applications' && styles.tabActive,
          ]}
          onPress={() => setActiveTab('applications')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'applications' && styles.tabTextActive,
            ]}
          >
            Заявки
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'assigned' && styles.tabActive,
          ]}
          onPress={() => setActiveTab('assigned')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'assigned' && styles.tabTextActive,
            ]}
          >
            Назначенные
          </Text>
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
        {activeTab === 'applications' ? (
          applications.length === 0 ? (
            <Card>
              <Text style={styles.emptyText}>Нет заявок</Text>
            </Card>
          ) : (
            applications.map((app) => renderOrderCard(app, true))
          )
        ) : (
          assignedOrders.length === 0 ? (
            <Card>
              <Text style={styles.emptyText}>Нет назначенных заказов</Text>
            </Card>
          ) : (
            assignedOrders.map((order) => renderOrderCard(order, false))
          )
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

      {/* Refuse Confirmation Modal */}
      <ConfirmationModal
        visible={showRefuseModal}
        title="Отказаться от заказа"
        message="Вы уверены, что хотите отказаться от заказа? Это повлечёт штрафные санкции."
        confirmText="Отказаться"
        cancelText="Отмена"
        onConfirm={handleRefuseAssignment}
        onCancel={() => setShowRefuseModal(false)}
        variant="danger"
      />

      <ToastContainer />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    padding: SPACING.l,
    paddingTop: SPACING.xl,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  title: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: '700',
    color: COLORS.primary,
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  tab: {
    flex: 1,
    paddingVertical: SPACING.m,
    alignItems: 'center',
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: COLORS.primary,
  },
  tabText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
    fontWeight: '500',
  },
  tabTextActive: {
    color: COLORS.primary,
    fontWeight: '600',
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
  },
  statusText: {
    fontSize: FONT_SIZES.s,
    fontWeight: '600',
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
  assignedActions: {
    flexDirection: 'row',
    gap: SPACING.m,
  },
  assignedAction: {
    flex: 1,
  },
});
