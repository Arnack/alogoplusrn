import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, Modal } from 'react-native';
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
  SearchOrders: undefined;
  MyOrders: undefined;
  Wallet: undefined;
  Profile: undefined;
  Notifications: undefined;
  Promotions: undefined;
  OrderDetails: { orderId: number; order: any };
};

type SearchOrdersScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'SearchOrders'>;

interface SearchOrdersScreenProps {
  navigation: SearchOrdersScreenNavigationProp;
}

interface CustomerItem {
  customer_id: number;
  organization: string;
  orders_available: number;
}

interface OrderItem {
  id: number;
  job_name: string;
  date: string;
  city: string;
  customer_id: number;
  day_shift: string | null;
  night_shift: string | null;
  amount_base: string;
  amount_with_rating: string;
  job_fp: string | null;
  travel_compensation_rub: number | null;
}

interface ConfirmState {
  orderId: number;
  summaryHtml: string;
  messageHtml: string;
}

function stripHtml(html: string): string {
  return html
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n')
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .trim();
}

export const SearchOrdersScreen: React.FC<SearchOrdersScreenProps> = ({ navigation }) => {
  const [customers, setCustomers] = useState<CustomerItem[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<number | null>(null);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [applyingOrderId, setApplyingOrderId] = useState<number | null>(null);
  const [confirm, setConfirm] = useState<ConfirmState | null>(null);
  const [confirming, setConfirming] = useState(false);
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const data = await apiService.getOrderCustomers();
      setCustomers(Array.isArray(data) ? data : (data as any)?.data || []);
    } catch (err: any) {
      error('Ошибка загрузки заказчиков');
    }
  };

  const loadOrders = async (customerId: number) => {
    setLoading(true);
    try {
      const data = await apiService.searchOrders(customerId);
      setOrders(Array.isArray(data) ? data : (data as any)?.data || []);
      setSelectedCustomer(customerId);
    } catch (err: any) {
      error('Ошибка загрузки заказов');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    if (selectedCustomer) {
      await loadOrders(selectedCustomer);
    } else {
      await loadCustomers();
    }
    setRefreshing(false);
  };

  const handleApplyPress = async (orderId: number) => {
    setApplyingOrderId(orderId);
    try {
      const preview = await apiService.getOrderApplyPreview(orderId);
      const previewData = (preview as any)?.data || preview;
      setConfirm({
        orderId,
        summaryHtml: previewData?.order_summary_html || '',
        messageHtml: previewData?.message_html || '',
      });
    } catch (err: any) {
      error(err.message || 'Ошибка загрузки');
    } finally {
      setApplyingOrderId(null);
    }
  };

  const handleConfirm = async () => {
    if (!confirm) return;
    setConfirming(true);
    try {
      await apiService.createOrderApplication(confirm.orderId);
      success('Заявка принята');
      setConfirm(null);
      if (selectedCustomer) {
        await loadOrders(selectedCustomer);
        await loadCustomers();
      }
    } catch (err: any) {
      error(err.message || 'Ошибка при отклике');
    } finally {
      setConfirming(false);
    }
  };

  const getShiftLabel = (order: OrderItem) => {
    if (order.day_shift) return `День  ${order.day_shift}`;
    if (order.night_shift) return `Ночь  ${order.night_shift}`;
    return '—';
  };

  const getShiftColor = (order: OrderItem) => {
    return order.day_shift ? COLORS.day : COLORS.night;
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Поиск заявок" onBack={() => navigation.goBack()} />

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
        {/* Customer Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Получатели услуг</Text>
          {customers.length === 0 ? (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyIcon}>🏢</Text>
              <Text style={styles.emptyText}>Нет доступных заказчиков</Text>
            </View>
          ) : (
            customers.map((customer) => {
              const isSelected = selectedCustomer === customer.customer_id;
              return (
                <TouchableOpacity
                  key={customer.customer_id}
                  style={[styles.customerCard, isSelected && styles.customerCardSelected]}
                  onPress={() => loadOrders(customer.customer_id)}
                  activeOpacity={0.75}
                >
                  <View style={[styles.customerIcon, isSelected && styles.customerIconSelected]}>
                    <Text style={styles.customerIconText}>🏢</Text>
                  </View>
                  <View style={styles.customerInfo}>
                    <Text style={[styles.customerName, isSelected && styles.customerNameSelected]} numberOfLines={2}>
                      {customer.organization}
                    </Text>
                  </View>
                  <View style={[styles.customerBadge, isSelected && styles.customerBadgeSelected]}>
                    <Text style={[styles.customerBadgeText, isSelected && styles.customerBadgeTextSelected]}>
                      {customer.orders_available}
                    </Text>
                    <Text style={[styles.customerBadgeLabel, isSelected && styles.customerBadgeTextSelected]}>
                      {customer.orders_available === 1 ? 'заявка' : customer.orders_available < 5 ? 'заявки' : 'заявок'}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            })
          )}
        </View>

        {/* Orders List */}
        {selectedCustomer !== null && (
          loading ? (
            <LoadingScreen text="Загрузка заявок..." />
          ) : (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>
                Заявки {orders.length > 0 && `(${orders.length})`}
              </Text>

              {orders.length === 0 ? (
                <Card>
                  <Text style={styles.emptyText}>Нет доступных заявок</Text>
                </Card>
              ) : (
                orders.map((order) => (
                  <Card key={order.id} style={styles.orderCard}>
                    <View style={styles.orderHeader}>
                      <View style={styles.orderHeaderLeft}>
                        <Text style={styles.orderJob}>{order.job_name}</Text>
                        <Text style={styles.orderCity}>{order.city}</Text>
                      </View>
                      <View style={styles.orderAmount}>
                        <Text style={styles.orderAmountValue}>{order.amount_with_rating} ₽</Text>
                        {order.travel_compensation_rub ? (
                          <Text style={styles.orderTravel}>+{order.travel_compensation_rub} ₽ 🚌</Text>
                        ) : null}
                      </View>
                    </View>

                    <View style={styles.orderDetails}>
                      <View style={styles.orderDetail}>
                        <Text style={styles.orderDetailLabel}>Дата</Text>
                        <Text style={styles.orderDetailValue}>{order.date}</Text>
                      </View>
                      <View style={styles.orderDetail}>
                        <Text style={styles.orderDetailLabel}>Смена</Text>
                        <View style={[styles.shiftBadge, { backgroundColor: getShiftColor(order) + '20' }]}>
                          <Text style={[styles.shiftBadgeText, { color: getShiftColor(order) }]}>
                            {getShiftLabel(order)}
                          </Text>
                        </View>
                      </View>
                    </View>

                    {order.job_fp ? (
                      <Text style={styles.jobFp}>{order.job_fp}</Text>
                    ) : null}

                    <Button
                      title="Взять заявку"
                      onPress={() => handleApplyPress(order.id)}
                      loading={applyingOrderId === order.id}
                      fullWidth
                      size="large"
                    />
                  </Card>
                ))
              )}
            </View>
          )
        )}

        {selectedCustomer === null && customers.length > 0 && (
          <Card>
            <Text style={styles.emptyText}>Выберите получателя услуг</Text>
          </Card>
        )}
      </ScrollView>

      {/* Confirmation Modal */}
      <Modal visible={confirm !== null} transparent animationType="fade" onRequestClose={() => setConfirm(null)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalBox}>
            <Text style={styles.modalTitle}>Подтверждение</Text>
            <ScrollView style={styles.modalScroll} showsVerticalScrollIndicator={false}>
              {confirm?.summaryHtml ? (
                <Text style={styles.modalSummary}>{stripHtml(confirm.summaryHtml)}</Text>
              ) : null}
              {confirm?.messageHtml ? (
                <Text style={styles.modalMessage}>{stripHtml(confirm.messageHtml)}</Text>
              ) : null}
            </ScrollView>
            <View style={styles.modalButtons}>
              <Button
                title="Отмена"
                variant="outline"
                onPress={() => setConfirm(null)}
                style={styles.modalBtn}
              />
              <Button
                title="Подтвердить"
                onPress={handleConfirm}
                loading={confirming}
                style={styles.modalBtn}
              />
            </View>
          </View>
        </View>
      </Modal>

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
  section: {
    marginBottom: SPACING.l,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.m,
  },
  customerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.l,
    padding: SPACING.m,
    marginBottom: SPACING.s,
    borderWidth: 1.5,
    borderColor: COLORS.border,
  },
  customerCardSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '08',
  },
  customerIcon: {
    width: 44,
    height: 44,
    borderRadius: BORDER_RADIUS.m,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  customerIconSelected: {
    backgroundColor: COLORS.primary + '18',
  },
  customerIconText: {
    fontSize: 22,
  },
  customerInfo: {
    flex: 1,
    marginRight: SPACING.s,
  },
  customerName: {
    fontSize: FONT_SIZES.m,
    fontWeight: '600',
    color: COLORS.text,
    lineHeight: 20,
  },
  customerNameSelected: {
    color: COLORS.primary,
  },
  customerBadge: {
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.m,
    paddingHorizontal: SPACING.s,
    paddingVertical: SPACING.xs,
    minWidth: 48,
  },
  customerBadgeSelected: {
    backgroundColor: COLORS.primary,
  },
  customerBadgeText: {
    fontSize: FONT_SIZES.l,
    fontWeight: '700',
    color: COLORS.text,
  },
  customerBadgeLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
  },
  customerBadgeTextSelected: {
    color: COLORS.white,
  },
  emptyCard: {
    alignItems: 'center',
    paddingVertical: SPACING.xl,
  },
  emptyIcon: {
    fontSize: 36,
    marginBottom: SPACING.s,
  },
  emptyText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
    textAlign: 'center',
  },
  orderCard: {
    marginBottom: SPACING.m,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.m,
  },
  orderHeaderLeft: {
    flex: 1,
    marginRight: SPACING.s,
  },
  orderJob: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
  },
  orderCity: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
  orderAmount: {
    alignItems: 'flex-end',
  },
  orderAmountValue: {
    fontSize: FONT_SIZES.xl,
    fontWeight: '700',
    color: COLORS.success,
  },
  orderTravel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.info,
    marginTop: SPACING.xs,
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
  jobFp: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    marginBottom: SPACING.m,
    lineHeight: 18,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.l,
  },
  modalBox: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    width: '100%',
    maxHeight: '80%',
    padding: SPACING.l,
  },
  modalTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.m,
  },
  modalScroll: {
    maxHeight: 300,
    marginBottom: SPACING.m,
  },
  modalSummary: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 22,
    marginBottom: SPACING.m,
  },
  modalMessage: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    lineHeight: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: SPACING.m,
  },
  modalBtn: {
    flex: 1,
  },
});
