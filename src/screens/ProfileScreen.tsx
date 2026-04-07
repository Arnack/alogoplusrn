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
import { Card, StatCard } from '../components/Card';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { LoadingScreen } from '../components/Loading';
import { CustomModal } from '../components/Modal';
import { ConfirmationModal } from '../components/Modal';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import { storage } from '../utils/storage';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Dashboard: undefined;
  Login: undefined;
  Profile: undefined;
};

type ProfileScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Profile'>;

interface ProfileScreenProps {
  navigation: ProfileScreenNavigationProp;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ navigation }) => {
  const [user, setUser] = useState<any>(null);
  const [rating, setRating] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [editingCard, setEditingCard] = useState(false);
  const [newCard, setNewCard] = useState('');
  const [showRules, setShowRules] = useState(false);
  const [showReferral, setShowReferral] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [referralInfo, setReferralInfo] = useState<any>(null);
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const [userResponse, ratingResponse] = await Promise.all([
        apiService.getMe(),
        apiService.getRating(),
      ]);
      setUser(userResponse.data);
      setRating(ratingResponse.data);
    } catch (err: any) {
      error('Ошибка загрузки профиля');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadProfile();
    setRefreshing(false);
  };

  const handleUpdateCard = async () => {
    if (!newCard || newCard.replace(/\s/g, '').length < 16) {
      error('Введите корректный номер карты');
      return;
    }

    try {
      await apiService.updateBankCard(newCard.replace(/\s/g, ''));
      success('Карта обновлена');
      setEditingCard(false);
      setNewCard('');
      await loadProfile();
    } catch (err: any) {
      error(err.message);
    }
  };

  const handleLogout = async () => {
    try {
      await apiService.logout();
    } catch (err) {
      // Ignore errors during logout
    }
    
    await storage.clearAll();
    success('Вы вышли из аккаунта');
    navigation.reset({
      index: 0,
      routes: [{ name: 'Login' }],
    });
  };

  const formatCardNumber = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    const formatted = cleaned.replace(/(\d{4})/g, '$1 ').trim();
    return formatted;
  };

  const handleCardChange = (text: string) => {
    const formatted = formatCardNumber(text);
    if (formatted.length <= 23) {
      setNewCard(formatted);
    }
  };

  if (loading) {
    return <LoadingScreen text="Загрузка профиля..." />;
  }

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Профиль" onBack={() => navigation.goBack()} />

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
        {/* User Info */}
        <Card style={styles.userCard}>
          <View style={styles.userInfo}>
            <View style={styles.userAvatar}>
              <Text style={styles.userAvatarText}>
                {user?.firstName?.charAt(0)}
                {user?.lastName?.charAt(0)}
              </Text>
            </View>
            <View style={styles.userDetails}>
              <Text style={styles.userName}>
                {user?.lastName} {user?.firstName}
              </Text>
              <Text style={styles.userCity}>{user?.city}</Text>
              <Text style={styles.userPhone}>{user?.phone}</Text>
            </View>
          </View>
        </Card>

        {/* Stats */}
        <Card>
          <View style={styles.statsRow}>
            <StatCard
              label="Рейтинг"
              value={rating?.coefficient || 1.0}
              icon="⭐"
              color={COLORS.warning}
            />
            <StatCard
              label="Баланс"
              value={`${user?.balance || 0} ₽`}
              icon="💰"
              color={COLORS.success}
            />
          </View>
          <View style={styles.statsRow}>
            <StatCard
              label="Всего заказов"
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

        {/* Personal Info */}
        <Card title="Личные данные">
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>ИНН</Text>
            <Text style={styles.infoValue}>{user?.inn}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Дата рождения</Text>
            <Text style={styles.infoValue}>{user?.birthday}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Статус</Text>
            <View
              style={[
                styles.statusBadge,
                {
                  backgroundColor: user?.isSelfEmployed
                    ? COLORS.success + '20'
                    : COLORS.error + '20',
                },
              ]}
            >
              <Text
                style={[
                  styles.statusText,
                  {
                    color: user?.isSelfEmployed
                      ? COLORS.success
                      : COLORS.error,
                  },
                ]}
              >
                {user?.isSelfEmployed ? 'Самозанятый' : 'Не подтверждено'}
              </Text>
            </View>
          </View>
        </Card>

        {/* Bank Card */}
        <Card title="Банковская карта">
          {editingCard ? (
            <>
              <Input
                label="Новый номер карты"
                value={newCard}
                onChangeText={handleCardChange}
                placeholder="0000 0000 0000 0000"
                keyboardType="number-pad"
                maxLength={23}
              />
              <View style={styles.cardActions}>
                <Button
                  title="Отмена"
                  onPress={() => {
                    setEditingCard(false);
                    setNewCard('');
                  }}
                  variant="outline"
                  style={styles.cardAction}
                />
                <Button
                  title="Сохранить"
                  onPress={handleUpdateCard}
                  style={styles.cardAction}
                />
              </View>
            </>
          ) : (
            <View style={styles.cardInfo}>
              <Text style={styles.cardNumber}>
                {user?.bankCard
                  ? `**** **** **** ${user.bankCard.slice(-4)}`
                  : 'Не указана'}
              </Text>
              <Button
                title={user?.bankCard ? 'Изменить карту' : 'Добавить карту'}
                onPress={() => setEditingCard(true)}
                variant="outline"
                size="small"
              />
            </View>
          )}
        </Card>

        {/* Actions */}
        <Card>
          <TouchableOpacity
            style={styles.actionItem}
            onPress={() => setShowRules(true)}
          >
            <Text style={styles.actionIcon}>📜</Text>
            <Text style={styles.actionText}>Правила</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionItem}
            onPress={() => setShowReferral(true)}
          >
            <Text style={styles.actionIcon}>🎁</Text>
            <Text style={styles.actionText}>Реферальная программа</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionItem}
            onPress={() => success('Обращение в поддержку')}
          >
            <Text style={styles.actionIcon}>💬</Text>
            <Text style={styles.actionText}>Поддержка</Text>
          </TouchableOpacity>
        </Card>

        {/* Logout */}
        <Button
          title="Выйти из аккаунта"
          onPress={() => setShowLogoutModal(true)}
          variant="danger"
          fullWidth
          style={styles.logoutButton}
        />
      </ScrollView>

      {/* Rules Modal */}
      <CustomModal
        visible={showRules}
        onClose={() => setShowRules(false)}
        title="Правила работы"
      >
        <Text style={styles.modalText}>
          1. На заказ необходимо явиться вовремя{'\n\n'}
          2. При отказе от назначенного заказа применяются штрафные санкции{'\n\n'}
          3. Минимальная сумма для вывода средств: 2600 ₽{'\n\n'}
          4. Рейтинг формируется на основе выполненных заказов{'\n\n'}
          5. За систематические отказы возможно блокировка аккаунта
        </Text>
      </CustomModal>

      {/* Referral Modal */}
      <CustomModal
        visible={showReferral}
        onClose={() => setShowReferral(false)}
        title="Реферальная программа"
      >
        <Text style={styles.modalText}>
          Пригласите друга и получите бонус за каждую отработанную смену!{'\n\n'}
          Ваша реферальная ссылка:{'\n'}
          <Text style={styles.referralLink}>
            https://t.me/Algoritmplus_bot?start=ref_{user?.id}
          </Text>
        </Text>
      </CustomModal>

      {/* Logout Confirmation */}
      <ConfirmationModal
        visible={showLogoutModal}
        title="Выход из аккаунта"
        message="Вы уверены, что хотите выйти?"
        confirmText="Выйти"
        cancelText="Отмена"
        onConfirm={handleLogout}
        onCancel={() => setShowLogoutModal(false)}
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
  userCard: {
    marginBottom: SPACING.l,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  userAvatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  userAvatarText: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: '700',
    color: COLORS.white,
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  userCity: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    marginBottom: SPACING.xs,
  },
  userPhone: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
  },
  statsRow: {
    flexDirection: 'row',
    gap: SPACING.m,
    marginBottom: SPACING.m,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.s,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  infoLabel: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
  },
  infoValue: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    fontWeight: '500',
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
  cardInfo: {
    alignItems: 'center',
  },
  cardNumber: {
    fontSize: FONT_SIZES.l,
    color: COLORS.text,
    fontWeight: '600',
    marginBottom: SPACING.m,
    letterSpacing: 2,
  },
  cardActions: {
    flexDirection: 'row',
    gap: SPACING.m,
  },
  cardAction: {
    flex: 1,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.m,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  actionIcon: {
    fontSize: FONT_SIZES.xl,
    marginRight: SPACING.m,
  },
  actionText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    fontWeight: '500',
  },
  logoutButton: {
    marginTop: SPACING.l,
    marginBottom: SPACING.xl,
  },
  modalText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 24,
  },
  referralLink: {
    color: COLORS.info,
    fontWeight: '600',
  },
});
