import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, Modal, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { Asset } from 'expo-asset';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { LoadingScreen } from '../components/Loading';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import { storage } from '../utils/storage';
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
  job_for_payment?: string | null;
  service_name?: string | null;
  service?: string | null;
  travel_compensation_rub: number | null;
}

interface ContractSignState {
  visible: boolean;
  pin: string;
  loading: boolean;
  pendingOrderId: number | null;
  pinType: string;
  pinHint: string;
  contractPdfUrl: string | null;
  contractLoading: boolean;
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

function getOrderJobFp(order: OrderItem): string {
  const value = order.job_fp || order.job_for_payment || order.service_name || order.service || '';
  return stripHtml(String(value));
}

export const SearchOrdersScreen: React.FC<SearchOrdersScreenProps> = ({ navigation }) => {
  const [customers, setCustomers] = useState<CustomerItem[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<number | null>(null);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [applyingOrderId, setApplyingOrderId] = useState<number | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [contractSign, setContractSign] = useState<ContractSignState>({
    visible: false,
    pin: '',
    loading: false,
    pendingOrderId: null,
    pinType: 'inn',
    pinHint: '',
    contractPdfUrl: null,
    contractLoading: false,
  });
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
      error('Ошибка загрузки заявок');
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
      // Always show contract signing modal first
      setApplyingOrderId(null);

      // Load contract PDF from local assets
      setContractSign({
        visible: true,
        pin: '',
        loading: false,
        pendingOrderId: orderId,
        pinType: 'inn',
        pinHint: 'последние 4 цифры ИНН, день и месяц рождения, год рождения или последние 4 цифры паспорта',
        contractPdfUrl: null,
        contractLoading: true,
      });

      try {
        // Load local PDF from assets
        const asset = Asset.fromModule(require('../../assets/pdf/agreement.pdf'));
        await asset.downloadAsync();
        const localUri = asset.localUri || asset.uri;

        setContractSign(prev => ({
          ...prev,
          contractPdfUrl: localUri,
          contractLoading: false,
        }));
      } catch (pdfErr) {
        console.error('Failed to load PDF:', pdfErr);
        // If PDF fails to load, still show the modal but without PDF
        setContractSign(prev => ({
          ...prev,
          contractLoading: false,
        }));
        error('Не удалось загрузить договор PDF, но вы можете продолжить');
      }
    } catch (err: any) {
      error(err.message || 'Ошибка загрузки');
      setApplyingOrderId(null);
    }
  };

  const handleContractSign = async () => {
    if (contractSign.pin.length !== 4) {
      error('Введите 4 последние цифры ИНН');
      return;
    }

    setContractSign(prev => ({ ...prev, loading: true }));
    try {
      // Sign contracts
      await apiService.ensureContracts(contractSign.pinType, contractSign.pin);

      // Mark contracts as signed in local storage
      await storage.set('has_signed_contracts', 'true');

      // Close contract modal
      const orderId = contractSign.pendingOrderId;
      setContractSign({ visible: false, pin: '', loading: false, pendingOrderId: null, pinType: 'inn', pinHint: '', contractPdfUrl: null, contractLoading: false });

      // Auto-accept the order after successful contract signing
      if (orderId) {
        setApplyingOrderId(orderId);
        await apiService.createOrderApplication(orderId);
        success('✓ Отклик отправлен');
        setApplyingOrderId(null);

        // Refresh orders list
        if (selectedCustomer) {
          await loadOrders(selectedCustomer);
          await loadCustomers();
        }
      }
    } catch (err: any) {
      error(err.message || 'Ошибка подписания договора');
    } finally {
      setApplyingOrderId(null);
      setContractSign(prev => ({ ...prev, loading: false }));
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
                orders.map((order) => {
                  const jobFp = getOrderJobFp(order);
                  return (
                  <Card key={order.id} style={styles.orderCard}>
                    <View style={styles.orderHeader}>
                      <View style={styles.orderHeaderLeft}>
                        <Text style={styles.orderJob}>{order.job_name}</Text>
                        <Text style={styles.orderCity}>{order.city}</Text>
                      </View>
                      <View style={styles.orderAmount}>
                        {order.amount_base && order.amount_with_rating && order.amount_base !== order.amount_with_rating ? (
                          <>
                            <Text style={styles.orderAmountBase}>{order.amount_base} ₽</Text>
                            <Text style={styles.orderAmountValue}>{order.amount_with_rating} ₽</Text>
                            <Text style={styles.orderRatingLabel}>рейтинг</Text>
                          </>
                        ) : (
                          <Text style={styles.orderAmountValue}>{order.amount_with_rating} ₽</Text>
                        )}
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
                        <Text style={styles.orderDetailLabel}>Период оказания услуг</Text>
                        <View style={[styles.shiftBadge, { backgroundColor: getShiftColor(order) + '20' }]}>
                          <Text style={[styles.shiftBadgeText, { color: getShiftColor(order) }]}>
                            {getShiftLabel(order)}
                          </Text>
                        </View>
                      </View>
                    </View>

                    {jobFp ? (
                      <Text style={styles.jobFp}>{jobFp}</Text>
                    ) : null}

                    <Button
                      title="Принять заявку"
                      onPress={() => handleApplyPress(order.id)}
                      loading={applyingOrderId === order.id}
                      fullWidth
                      size="large"
                    />
                  </Card>
                  );
                })
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

      {/* Contract Signing Modal */}
      <Modal visible={contractSign.visible} transparent animationType="fade" onRequestClose={() => {
        setContractSign(prev => ({ ...prev, visible: false }));
      }}>
        <View style={styles.contractModalOverlay}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.contractKeyboardAvoid}
          >
            <View style={styles.contractModalBox}>
              <View style={styles.contractModalHeader}>
                <Text style={styles.contractModalTitle}>Подписание договора</Text>
                <TouchableOpacity onPress={() => {
                  setContractSign(prev => ({ ...prev, visible: false }));
                }}>
                  <Ionicons name="close" size={24} color={COLORS.white} />
                </TouchableOpacity>
              </View>

              <ScrollView
                style={styles.contractModalScroll}
                showsVerticalScrollIndicator={false}
                keyboardShouldPersistTaps="handled"
              >
                {/* Contract PDF Download Button */}
                {contractSign.contractLoading ? (
                  <View style={styles.contractLoadingBox}>
                    <Text style={styles.contractLoadingText}>Загрузка договора PDF...</Text>
                  </View>
                ) : contractSign.contractPdfUrl ? (
                  <TouchableOpacity
                    style={styles.contractDownloadBox}
                    activeOpacity={0.7}
                    onPress={async () => {
                      try {
                        await Sharing.shareAsync(contractSign.contractPdfUrl!, {
                          mimeType: 'application/pdf',
                          UTI: 'com.adobe.pdf',
                        });
                      } catch (err) {
                        error('Не удалось открыть PDF');
                      }
                    }}
                  >
                    <Ionicons name="document-text-outline" size={28} color={COLORS.primary} />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.contractDownloadText}>Открыть договор PDF</Text>
                      <Text style={styles.contractDownloadHint}>Нажмите для просмотра документа</Text>
                    </View>
                    <Ionicons name="open-outline" size={24} color={COLORS.gray} />
                  </TouchableOpacity>
                ) : null}

                {/* Contract Text - Exact text from Telegram bot */}
                <View style={styles.contractTextBox}>
                  <Text style={styles.contractTextBlock}>
                    📄 Для принятия Заявки необходимо заключить гражданско-правовой договор.
                  </Text>

                  <Text style={styles.contractTextBlock}>
                    Подписание — ввод 4 цифр одного из ваших идентификаторов.
                  </Text>

                  <Text style={styles.contractTextBlock}>
                    Подтверждая подписание договора и принятие Заявки, вы подтверждаете, что:
                  </Text>

                  <Text style={styles.contractBulletPoint}>
                    • действуете добровольно, самостоятельно и в своих интересах;
                  </Text>
                  <Text style={styles.contractBulletPoint}>
                    • самостоятельно принимаете решение об оказании услуг;
                  </Text>
                  <Text style={styles.contractBulletPoint}>
                    • оказываете услуги в рамках гражданско-правового договора;
                  </Text>
                  <Text style={styles.contractBulletPoint}>
                    • не состоите и не вступаете в трудовые отношения с Платформой и Получателем услуг;
                  </Text>
                  <Text style={styles.contractBulletPoint}>
                    • не подчиняетесь правилам внутреннего трудового распорядка;
                  </Text>
                  <Text style={styles.contractBulletPoint}>
                    • самостоятельно организуете оказание услуг и несёте соответствующие риски;
                  </Text>
                  <Text style={styles.contractBulletPoint}>
                    • ознакомлены и согласны с условиями договора и Заявки.
                  </Text>

                  <Text style={styles.contractTextBlock}>
                    ⚖️ Платформа является информационной системой и не выступает работодателем,
                    {'\n'}заказчиком услуг или платёжным агентом.
                  </Text>

                  <Text style={styles.contractWarningText}>
                    ❗ Без подписания договора принятие Заявки невозможно.
                  </Text>
                </View>

                {/* Divider */}
                <View style={styles.contractDivider} />

                {/* PIN Input Section */}
                <Text style={styles.contractPinTitle}>
                  Введите 4 последние цифры ИНН:
                </Text>
                <View style={styles.contractPinInputWrapper}>
                  <TextInput
                    style={styles.contractPinInput}
                    value={contractSign.pin}
                    onChangeText={(text) => setContractSign(prev => ({ ...prev, pin: text.replace(/\D/g, '').slice(0, 4) }))}
                    placeholder="••••"
                    keyboardType="number-pad"
                    maxLength={4}
                    textAlign="center"
                    placeholderTextColor={COLORS.gray}
                  />
                </View>

                <Button
                  title="Подтвердить"
                  onPress={handleContractSign}
                  loading={contractSign.loading}
                  fullWidth
                  size="large"
                  style={styles.contractSubmitBtn}
                />
              </ScrollView>
            </View>
          </KeyboardAvoidingView>
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
  orderAmountBase: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    textDecorationLine: 'line-through',
    marginBottom: 2,
  },
  orderRatingLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.info,
    marginTop: SPACING.xs,
    fontStyle: 'italic',
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
  contractModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.l,
  },
  contractKeyboardAvoid: {
    flex: 1,
    justifyContent: 'center',
    width: '100%',
    maxHeight: '90%',
  },
  contractModalBox: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    width: '100%',
    maxHeight: '90%',
    overflow: 'hidden',
  },
  contractModalHeader: {
    backgroundColor: COLORS.primary,
    padding: SPACING.l,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  contractModalTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '700',
    color: COLORS.white,
  },
  contractModalScroll: {
    padding: SPACING.l,
    paddingTop: SPACING.m,
  },
  contractLoadingBox: {
    padding: SPACING.l,
    alignItems: 'center',
    marginBottom: SPACING.l,
  },
  contractLoadingText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
  },
  contractDownloadBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '10',
    padding: SPACING.m,
    borderRadius: BORDER_RADIUS.l,
    marginBottom: SPACING.l,
    gap: SPACING.m,
    borderWidth: 1,
    borderColor: COLORS.primary + '30',
  },
  contractDownloadText: {
    fontSize: FONT_SIZES.m,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 2,
  },
  contractDownloadHint: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
  },
  contractTextBox: {
    marginBottom: SPACING.l,
  },
  contractTextBlock: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 24,
    marginBottom: SPACING.m,
  },
  contractBulletPoint: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 24,
    marginLeft: SPACING.m,
    marginBottom: SPACING.xs,
  },
  contractWarningText: {
    fontSize: FONT_SIZES.m,
    fontWeight: '600',
    color: COLORS.error,
    marginTop: SPACING.m,
    marginBottom: SPACING.m,
    lineHeight: 24,
  },
  contractDivider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginVertical: SPACING.l,
  },
  contractPinTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.m,
    textAlign: 'center',
  },
  contractPinInputWrapper: {
    marginBottom: SPACING.l,
  },
  contractPinInput: {
    fontSize: FONT_SIZES.xxxl,
    fontWeight: '700',
    color: COLORS.text,
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.l,
    paddingVertical: SPACING.l,
    paddingHorizontal: SPACING.xl,
    borderWidth: 2,
    borderColor: COLORS.border,
    letterSpacing: 8,
  },
  contractSubmitBtn: {
    marginTop: SPACING.m,
  },
});
