import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS, MINIMUM_PAYOUT } from '../constants';
import { Card, StatCard } from '../components/Card';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { LoadingScreen } from '../components/Loading';
import { ConfirmationModal } from '../components/Modal';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Dashboard: undefined;
  Wallet: undefined;
};

type WalletScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Wallet'>;

interface WalletScreenProps {
  navigation: WalletScreenNavigationProp;
}

export const WalletScreen: React.FC<WalletScreenProps> = ({ navigation }) => {
  const [balance, setBalance] = useState(0);
  const [paymentHistory, setPaymentHistory] = useState<any[]>([]);
  const [walletPayments, setWalletPayments] = useState<any[]>([]);
  const [payoutAmount, setPayoutAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [creatingPayout, setCreatingPayout] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    loadWalletData();
  }, []);

  const loadWalletData = async () => {
    try {
      const panel = await apiService.getProfileAboutPanel();
      const panelData = (panel as any)?.data || panel;
      const raw: string = panelData?.balance || '0';
      setBalance(parseFloat(raw.replace(',', '.')) || 0);
      setPaymentHistory([]);
      setWalletPayments([]);
    } catch (err: any) {
      error('Ошибка загрузки данных кошелька');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadWalletData();
    setRefreshing(false);
  };

  const handlePayout = () => {
    const amount = parseInt(payoutAmount.replace(/\D/g, ''), 10);
    
    if (isNaN(amount)) {
      error('Введите сумму');
      return;
    }

    if (amount < MINIMUM_PAYOUT) {
      error(`Минимальная сумма вывода ${MINIMUM_PAYOUT} ₽`);
      return;
    }

    if (amount > balance) {
      error('Недостаточно средств');
      return;
    }

    setShowConfirmModal(true);
  };

  const confirmPayout = async () => {
    const amount = parseInt(payoutAmount.replace(/\D/g, ''), 10);
    setCreatingPayout(true);
    
    try {
      await apiService.createPayment(amount);
      success('Заявка на выплату создана');
      setPayoutAmount('');
      await loadWalletData();
    } catch (err: any) {
      error(err.message);
    } finally {
      setCreatingPayout(false);
      setShowConfirmModal(false);
    }
  };

  const formatAmount = (amount: string) => {
    const cleaned = amount.replace(/\D/g, '');
    return cleaned.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  };

  const handleAmountChange = (text: string) => {
    const formatted = formatAmount(text);
    setPayoutAmount(formatted);
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Кошелёк" onBack={() => navigation.goBack()} />

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
        {/* Balance Card */}
        <Card style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>Текущий баланс</Text>
          <Text style={styles.balanceValue}>{balance.toLocaleString('ru-RU')} ₽</Text>
        </Card>

        {/* Payout Form */}
        <Card title="Вывод средств" subtitle={`Минимум ${MINIMUM_PAYOUT} ₽`}>
          <Input
            label="Сумма вывода"
            value={payoutAmount}
            onChangeText={handleAmountChange}
            placeholder="Введите сумму"
            keyboardType="number-pad"
            hint={`Доступно: ${balance.toLocaleString('ru-RU')} ₽`}
          />

          <Button
            title="Создать заявку"
            onPress={handlePayout}
            loading={creatingPayout}
            fullWidth
            size="large"
            disabled={balance < MINIMUM_PAYOUT}
          />
        </Card>

        {/* Wallet Payments */}
        <Card title="Заявки на вывод">
          {walletPayments.length === 0 ? (
            <Text style={styles.emptyText}>Нет заявок на вывод</Text>
          ) : (
            walletPayments.map((payment) => (
              <View key={payment.id} style={styles.paymentItem}>
                <View style={styles.paymentInfo}>
                  <Text style={styles.paymentAmount}>{payment.amount.toLocaleString('ru-RU')} ₽</Text>
                  <Text style={styles.paymentDate}>{payment.createdAt}</Text>
                </View>
                <View
                  style={[
                    styles.paymentStatus,
                    {
                      backgroundColor:
                        payment.status === 'completed'
                          ? COLORS.success + '20'
                          : payment.status === 'pending'
                          ? COLORS.warning + '20'
                          : COLORS.error + '20',
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.paymentStatusText,
                      {
                        color:
                          payment.status === 'completed'
                            ? COLORS.success
                            : payment.status === 'pending'
                            ? COLORS.warning
                            : COLORS.error,
                      },
                    ]}
                  >
                    {payment.status === 'completed'
                      ? 'Выполнено'
                      : payment.status === 'pending'
                      ? 'В обработке'
                      : 'Отклонено'}
                  </Text>
                </View>
              </View>
            ))
          )}
        </Card>

        {/* Payment History */}
        <Card title="История платежей">
          {paymentHistory.length === 0 ? (
            <Text style={styles.emptyText}>История пуста</Text>
          ) : (
            paymentHistory.map((payment) => (
              <View key={payment.id} style={styles.paymentItem}>
                <View style={styles.paymentInfo}>
                  <Text style={styles.paymentAmount}>
                    +{payment.amount.toLocaleString('ru-RU')} ₽
                  </Text>
                  <Text style={styles.paymentDate}>{payment.date}</Text>
                </View>
                <View style={styles.paymentType}>
                  <Text style={styles.paymentTypeText}>
                    {payment.type === 'order'
                      ? 'Заказ'
                      : payment.type === 'bonus'
                      ? 'Бонус'
                      : 'Реферал'}
                  </Text>
                </View>
              </View>
            ))
          )}
        </Card>
      </ScrollView>

      {/* Confirmation Modal */}
      <ConfirmationModal
        visible={showConfirmModal}
        title="Подтверждение вывода"
        message={`Вы хотите вывести ${parseInt(payoutAmount.replace(/\D/g, ''), 10).toLocaleString('ru-RU')} ₽ на карту?\n\nСредства поступят после обработки бухгалтером.`}
        confirmText="Подтвердить"
        cancelText="Отмена"
        onConfirm={confirmPayout}
        onCancel={() => setShowConfirmModal(false)}
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
  balanceCard: {
    marginBottom: SPACING.l,
    alignItems: 'center',
    padding: SPACING.xl,
  },
  balanceLabel: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
    marginBottom: SPACING.s,
  },
  balanceValue: {
    fontSize: FONT_SIZES.xxxl,
    fontWeight: '700',
    color: COLORS.success,
  },
  emptyText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
    textAlign: 'center',
    padding: SPACING.xl,
  },
  paymentItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.m,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  paymentInfo: {
    flex: 1,
  },
  paymentAmount: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
  },
  paymentDate: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
  paymentStatus: {
    paddingHorizontal: SPACING.m,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.round,
  },
  paymentStatusText: {
    fontSize: FONT_SIZES.s,
    fontWeight: '600',
  },
  paymentType: {
    paddingHorizontal: SPACING.m,
    paddingVertical: SPACING.xs,
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.s,
  },
  paymentTypeText: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    fontWeight: '500',
  },
});
