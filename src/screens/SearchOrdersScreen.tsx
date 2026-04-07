import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS, SHIFT_TIMES } from '../constants';
import { Card, StatCard } from '../components/Card';
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

export const SearchOrdersScreen: React.FC<SearchOrdersScreenProps> = ({ navigation }) => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<number | null>(null);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [applyingOrderId, setApplyingOrderId] = useState<number | null>(null);
  const { success, error, warning, ToastContainer } = useToast();

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await apiService.getOrderCustomers();
      setCustomers(response.data);
    } catch (err: any) {
      error('Ошибка загрузки заказчиков');
    }
  };

  const loadOrders = async (customerId: number) => {
    setLoading(true);
    try {
      const response = await apiService.searchOrders(customerId);
      setOrders(response.data);
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

  const handleApply = async (orderId: number) => {
    setApplyingOrderId(orderId);
    try {
      // Preview
      await apiService.getOrderApplyPreview(orderId);
      
      // Apply
      await apiService.createOrderApplication(orderId);
      success('Заявка создана');
      
      // Reload orders
      if (selectedCustomer) {
        await loadOrders(selectedCustomer);
      }
    } catch (err: any) {
      error(err.message);
    } finally {
      setApplyingOrderId(null);
    }
  };

  const getShiftColor = (shift: string) => {
    return shift === 'day' ? COLORS.day : COLORS.night;
  };

  const getCustomerName = (customerId: number) => {
    return customers.find((c) => c.id === customerId)?.name || '';
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
          <Text style={styles.sectionTitle}>Заказчики</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.customersScroll}>
            {customers.map((customer) => (
              <TouchableOpacity
                key={customer.id}
                style={[
                  styles.customerChip,
                  selectedCustomer === customer.id && styles.customerChipSelected,
                ]}
                onPress={() => loadOrders(customer.id)}
              >
                <Text
                  style={[
                    styles.customerChipText,
                    selectedCustomer === customer.id && styles.customerChipTextSelected,
                  ]}
                >
                  {customer.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Orders List */}
        {loading ? (
          <LoadingScreen text="Загрузка заказов..." />
        ) : (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              Доступные заказы {orders.length > 0 && `(${orders.length})`}
            </Text>
            
            {orders.length === 0 ? (
              <Card>
                <Text style={styles.emptyText}>Нет доступных заказов</Text>
              </Card>
            ) : (
              orders.map((order) => (
                <Card key={order.id} style={styles.orderCard}>
                  <View style={styles.orderHeader}>
                    <View>
                      <Text style={styles.orderCustomer}>{order.customerName}</Text>
                      <Text style={styles.orderJob}>{order.jobName}</Text>
                    </View>
                    <View style={styles.orderAmount}>
                      <Text style={styles.orderAmountValue}>{order.adjustedAmount || order.amount} ₽</Text>
                    </View>
                  </View>

                  <View style={styles.orderDetails}>
                    <View style={styles.orderDetail}>
                      <Text style={styles.orderDetailLabel}>Дата</Text>
                      <Text style={styles.orderDetailValue}>{order.date}</Text>
                    </View>
                    <View style={styles.orderDetail}>
                      <Text style={styles.orderDetailLabel}>Смена</Text>
                      <View style={[
                        styles.shiftBadge,
                        { backgroundColor: getShiftColor(order.shift) + '20' },
                      ]}>
                        <Text style={[
                          styles.shiftBadgeText,
                          { color: getShiftColor(order.shift) },
                        ]}>
                          {order.shift === 'day' ? 'День' : 'Ночь'}
                        </Text>
                      </View>
                    </View>
                    <View style={styles.orderDetail}>
                      <Text style={styles.orderDetailLabel}>Город</Text>
                      <Text style={styles.orderDetailValue}>{order.city}</Text>
                    </View>
                    <View style={styles.orderDetail}>
                      <Text style={styles.orderDetailLabel}>Места</Text>
                      <Text style={styles.orderDetailValue}>
                        {order.workersCount}/{order.workersRequired}
                      </Text>
                    </View>
                  </View>

                  <Button
                    title="Взять заказ"
                    onPress={() => handleApply(order.id)}
                    loading={applyingOrderId === order.id}
                    fullWidth
                    size="large"
                  />
                </Card>
              ))
            )}
          </View>
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
  customersScroll: {
    flexDirection: 'row',
  },
  customerChip: {
    paddingHorizontal: SPACING.m,
    paddingVertical: SPACING.s,
    borderRadius: BORDER_RADIUS.round,
    backgroundColor: COLORS.background,
    marginRight: SPACING.s,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  customerChipSelected: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  customerChipText: {
    fontSize: FONT_SIZES.s,
    color: COLORS.text,
  },
  customerChipTextSelected: {
    color: COLORS.white,
    fontWeight: '500',
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
  orderAmount: {
    alignItems: 'flex-end',
  },
  orderAmountValue: {
    fontSize: FONT_SIZES.xl,
    fontWeight: '700',
    color: COLORS.success,
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
});
