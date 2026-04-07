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
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { LoadingScreen } from '../components/Loading';
import { CustomModal, ConfirmationModal } from '../components/Modal';
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

// AboutPanelOut fields:
// phone_registry, fio_registry, phone_actual, fio_actual,
// card, balance, city, rating, total_orders, successful_orders, in_rr

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ navigation }) => {
  const [panel, setPanel] = useState<any>(null);
  const [me, setMe] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [editingCard, setEditingCard] = useState(false);
  const [newCard, setNewCard] = useState('');
  const [innLast4, setInnLast4] = useState('');
  const [showRules, setShowRules] = useState(false);
  const [rulesText, setRulesText] = useState('');
  const [rulesLoading, setRulesLoading] = useState(false);
  const [showReferral, setShowReferral] = useState(false);
  const [referralLink, setReferralLink] = useState('');
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [showCityModal, setShowCityModal] = useState(false);
  const [cities, setCities] = useState<{ id: number; name: string }[]>([]);
  const [citySearch, setCitySearch] = useState('');
  const [cityLoading, setCityLoading] = useState(false);
  const { success, error, ToastContainer } = useToast();

  const loadProfile = useCallback(async () => {
    try {
      const [panelRes, meRes] = await Promise.all([
        apiService.getProfileAboutPanel(),
        apiService.getMe(),
      ]);
      setPanel(panelRes);
      setMe(meRes);
    } catch {
      error('Ошибка загрузки профиля');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadProfile(); }, [loadProfile]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadProfile();
    setRefreshing(false);
  };

  const handleOpenRules = async () => {
    setShowRules(true);
    if (!rulesText) {
      setRulesLoading(true);
      try {
        const res = await apiService.getWorkerRules();
        const raw = res?.text || res?.data?.text || 'Правила не найдены.';
        setRulesText(raw.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim());
      } catch {
        setRulesText('Не удалось загрузить правила.');
      } finally {
        setRulesLoading(false);
      }
    }
  };

  const handleOpenReferral = async () => {
    setShowReferral(true);
    if (!referralLink) {
      try {
        const res = await apiService.getReferralInfo();
        setReferralLink(res?.link || res?.data?.link || '');
      } catch {
        setReferralLink('');
      }
    }
  };

  const handleUpdateCard = async () => {
    const cleaned = newCard.replace(/\s/g, '');
    if (cleaned.length < 16) {
      error('Введите корректный номер карты');
      return;
    }
    if (innLast4.length !== 4) {
      error('Введите последние 4 цифры ИНН');
      return;
    }
    try {
      await apiService.updateBankCard(cleaned, innLast4);
      success('Карта обновлена');
      setEditingCard(false);
      setNewCard('');
      setInnLast4('');
      loadProfile();
    } catch (err: any) {
      error(err.message);
    }
  };

  const handleOpenCityModal = async () => {
    setShowCityModal(true);
    setCitySearch('');
    if (cities.length === 0) {
      setCityLoading(true);
      try {
        const result = await apiService.getCities();
        const data = (result as any)?.data ?? result;
        if (Array.isArray(data)) setCities(data.filter((c: any) => c.id && c.name).map((c: any) => ({ id: c.id, name: c.name })));
      } catch {
        error('Не удалось загрузить города');
      } finally {
        setCityLoading(false);
      }
    }
  };

  const handleSelectCity = async (cityId: number, cityName: string) => {
    try {
      await apiService.requestCityChange(cityId);
      success(`Запрос на смену города «${cityName}» отправлен`);
      setShowCityModal(false);
    } catch (err: any) {
      error(err.message || 'Ошибка отправки запроса');
    }
  };

  const handleLogout = async () => {
    try { await apiService.logout(); } catch {}
    await storage.clearAll();
    navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
  };

  const handleCardChange = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    const formatted = cleaned.replace(/(\d{4})/g, '$1 ').trim();
    if (formatted.length <= 23) setNewCard(formatted);
  };

  if (loading) return <LoadingScreen text="Загрузка профиля..." />;

  // fio_actual = "Фамилия Имя Отчество"
  const fio = (panel?.fio_actual || panel?.fio_registry || '').trim();
  const parts = fio.split(/\s+/);
  const initials = `${parts[0]?.[0] ?? ''}${parts[1]?.[0] ?? ''}`.toUpperCase();

  const stats = [
    { label: 'Баланс', value: `${panel?.balance ?? 0} ₽`, icon: 'cash-outline' as const, color: '#27AE60', bg: '#EAFAF1' },
    { label: 'Рейтинг', value: panel?.rating ?? '—', icon: 'star-outline' as const, color: '#F39C12', bg: '#FEF9E7' },
    { label: 'Заказов', value: String(panel?.total_orders ?? 0), icon: 'briefcase-outline' as const, color: '#4A90D9', bg: '#EBF4FF' },
    { label: 'Выполнено', value: String(panel?.successful_orders ?? 0), icon: 'checkmark-circle-outline' as const, color: '#7B68EE', bg: '#F0EEFF' },
  ];

  const infoRows = [
    { label: 'Телефон (реестр)', value: panel?.phone_registry || '—' },
    { label: 'Телефон (факт.)', value: panel?.phone_actual || '—' },
    { label: 'ФИО (реестр)', value: panel?.fio_registry || '—' },
    { label: 'ФИО (факт.)', value: panel?.fio_actual || '—' },
    { label: 'ИНН', value: me?.inn_masked || '—' },
  ];

  const actions = [
    { icon: 'document-text-outline' as const, label: 'Правила работы', onPress: handleOpenRules },
    { icon: 'gift-outline' as const, label: 'Реферальная программа', onPress: handleOpenReferral },
    { icon: 'chatbubble-outline' as const, label: 'Поддержка', onPress: () => success('Обращение направлено') },
  ];

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Профиль" onBack={() => navigation.goBack()} />

      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} tintColor={COLORS.primary} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero */}
        <View style={styles.hero}>
          <View style={styles.avatar}>
            {initials ? (
              <Text style={styles.avatarText}>{initials}</Text>
            ) : (
              <Ionicons name="person" size={32} color={COLORS.white} />
            )}
          </View>
          <Text style={styles.heroName}>{fio || '—'}</Text>
          <View style={styles.heroBadgeRow}>
            {panel?.in_rr && (
              <View style={styles.heroBadge}>
                <Ionicons name="checkmark-circle" size={13} color="#27AE60" />
                <Text style={[styles.heroBadgeText, { color: '#27AE60' }]}>Самозанятый</Text>
              </View>
            )}
            {panel?.city && (
              <View style={styles.heroBadge}>
                <Ionicons name="location-outline" size={13} color={COLORS.gray} />
                <Text style={styles.heroBadgeText}>{panel.city}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Stats strip */}
        <View style={styles.statsCard}>
          {stats.map((s, i) => (
            <React.Fragment key={s.label}>
              <View style={styles.statItem}>
                <View style={[styles.statIcon, { backgroundColor: s.bg }]}>
                  <Ionicons name={s.icon} size={16} color={s.color} />
                </View>
                <Text style={styles.statValue}>{s.value}</Text>
                <Text style={styles.statLabel}>{s.label}</Text>
              </View>
              {i < 3 && <View style={styles.statDivider} />}
            </React.Fragment>
          ))}
        </View>

        {/* Personal info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Личные данные</Text>
          <View style={styles.card}>
            {infoRows.map((row) => (
              <View key={row.label} style={styles.infoRow}>
                <Text style={styles.infoLabel}>{row.label}</Text>
                <Text style={styles.infoValue} numberOfLines={1}>{row.value}</Text>
              </View>
            ))}
            <TouchableOpacity style={styles.infoRow} onPress={handleOpenCityModal} activeOpacity={0.7}>
              <Text style={styles.infoLabel}>Город</Text>
              <View style={styles.infoValueRow}>
                <Text style={[styles.infoValue, { maxWidth: undefined }]}>{panel?.city || '—'}</Text>
                <Ionicons name="pencil-outline" size={14} color={COLORS.primary} style={{ marginLeft: 4 }} />
              </View>
            </TouchableOpacity>
            <View style={[styles.infoRow, styles.infoRowLast]}>
              <Text style={styles.infoLabel}>Статус</Text>
              <View style={[styles.statusBadge, { backgroundColor: panel?.in_rr ? '#EAFAF1' : '#FDEDEC' }]}>
                <Text style={[styles.statusText, { color: panel?.in_rr ? '#27AE60' : COLORS.error }]}>
                  {panel?.in_rr ? 'Самозанятый' : 'Не подтверждено'}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Bank card */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Банковская карта</Text>
          {editingCard ? (
            <View style={[styles.card, { padding: SPACING.m }]}>
              <Input
                label="Номер карты"
                value={newCard}
                onChangeText={handleCardChange}
                placeholder="0000 0000 0000 0000"
                keyboardType="number-pad"
                maxLength={23}
              />
              <Input
                label="Последние 4 цифры ИНН"
                value={innLast4}
                onChangeText={(t) => setInnLast4(t.replace(/\D/g, '').slice(0, 4))}
                placeholder="1234"
                keyboardType="number-pad"
                maxLength={4}
              />
              <View style={styles.cardActions}>
                <Button title="Отмена" onPress={() => { setEditingCard(false); setNewCard(''); setInnLast4(''); }} variant="outline" style={styles.cardAction} />
                <Button title="Сохранить" onPress={handleUpdateCard} style={styles.cardAction} />
              </View>
            </View>
          ) : (
            <TouchableOpacity style={styles.bankCard} onPress={() => setEditingCard(true)} activeOpacity={0.85}>
              <View>
                <Text style={styles.bankCardLabel}>Номер карты</Text>
                <Text style={styles.bankCardNumber}>
                  {panel?.card ? `•••• •••• •••• ${String(panel.card).slice(-4)}` : 'Не указана'}
                </Text>
              </View>
              <View style={styles.bankCardEditBtn}>
                <Ionicons name="pencil-outline" size={18} color={COLORS.white} />
              </View>
            </TouchableOpacity>
          )}
        </View>

        {/* Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Прочее</Text>
          <View style={styles.card}>
            {actions.map((item, i) => (
              <TouchableOpacity
                key={item.label}
                style={[styles.actionRow, i === actions.length - 1 && styles.actionRowLast]}
                onPress={item.onPress}
                activeOpacity={0.7}
              >
                <View style={styles.actionIconWrap}>
                  <Ionicons name={item.icon} size={20} color={COLORS.primary} />
                </View>
                <Text style={styles.actionLabel}>{item.label}</Text>
                <Ionicons name="chevron-forward" size={18} color={COLORS.gray} />
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutBtn} onPress={() => setShowLogoutModal(true)} activeOpacity={0.8}>
          <Ionicons name="log-out-outline" size={20} color={COLORS.error} />
          <Text style={styles.logoutText}>Выйти из аккаунта</Text>
        </TouchableOpacity>

        <View style={{ height: SPACING.xl }} />
      </ScrollView>

      <CustomModal visible={showRules} onClose={() => setShowRules(false)} title="Правила работы">
        <Text style={styles.modalText}>{rulesLoading ? 'Загрузка...' : (rulesText || 'Правила не найдены.')}</Text>
      </CustomModal>

      <CustomModal visible={showReferral} onClose={() => setShowReferral(false)} title="Реферальная программа">
        <Text style={styles.modalText}>Пригласите друга и получите бонус за каждую отработанную смену!</Text>
        {referralLink ? (
          <View style={styles.referralBox}>
            <Text style={styles.referralCode}>{referralLink}</Text>
          </View>
        ) : null}
      </CustomModal>

      <CustomModal
        visible={showCityModal}
        onClose={() => { setShowCityModal(false); setCitySearch(''); }}
        title="Сменить город"
      >
        <Text style={styles.cityModalHint}>
          Запрос будет отправлен менеджеру на подтверждение
        </Text>
        <Input
          label=""
          value={citySearch}
          onChangeText={setCitySearch}
          placeholder="Поиск города"
        />
        <ScrollView style={styles.cityList} nestedScrollEnabled showsVerticalScrollIndicator={false}>
          {cityLoading ? (
            <Text style={styles.cityModalHint}>Загрузка...</Text>
          ) : cities.filter(c => c.name?.toLowerCase().includes(citySearch.toLowerCase())).map((c) => (
            <View key={c.id} style={styles.cityItem}>
              <Button
                title={c.name}
                onPress={() => handleSelectCity(c.id, c.name)}
                variant={panel?.city === c.name ? 'primary' : 'outline'}
                fullWidth
                size="medium"
              />
            </View>
          ))}
        </ScrollView>
      </CustomModal>

      <ConfirmationModal
        visible={showLogoutModal}
        title="Выход"
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
  container: { flex: 1, backgroundColor: '#F4F6FA' },
  scroll: { paddingBottom: SPACING.xl },

  /* Hero */
  hero: {
    backgroundColor: COLORS.white,
    alignItems: 'center',
    paddingTop: SPACING.xl,
    paddingBottom: SPACING.l,
    paddingHorizontal: SPACING.l,
    borderBottomWidth: 1,
    borderBottomColor: '#EAECF0',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.m,
  },
  avatarText: { fontSize: FONT_SIZES.xxl, fontWeight: '800', color: COLORS.white },
  heroName: { fontSize: FONT_SIZES.xl, fontWeight: '700', color: COLORS.text, marginBottom: SPACING.s, textAlign: 'center' },
  heroBadgeRow: { flexDirection: 'row', gap: SPACING.s, flexWrap: 'wrap', justifyContent: 'center' },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#F4F6FA',
    borderRadius: BORDER_RADIUS.round,
    paddingHorizontal: SPACING.m,
    paddingVertical: 4,
  },
  heroBadgeText: { fontSize: FONT_SIZES.xs, color: COLORS.gray },

  /* Stats strip */
  statsCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.white,
    marginHorizontal: SPACING.l,
    marginTop: SPACING.l,
    borderRadius: BORDER_RADIUS.xl,
    paddingVertical: SPACING.m,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statItem: { flex: 1, alignItems: 'center', gap: 4 },
  statDivider: { width: 1, backgroundColor: '#EAECF0', marginVertical: 4 },
  statIcon: { width: 32, height: 32, borderRadius: BORDER_RADIUS.m, alignItems: 'center', justifyContent: 'center', marginBottom: 2 },
  statValue: { fontSize: FONT_SIZES.m, fontWeight: '700', color: COLORS.text },
  statLabel: { fontSize: 10, color: COLORS.gray, textAlign: 'center' },

  /* Section */
  section: { marginTop: SPACING.l, paddingHorizontal: SPACING.l },
  sectionTitle: {
    fontSize: FONT_SIZES.xs,
    fontWeight: '600',
    color: COLORS.gray,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: SPACING.s,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },

  /* Info rows */
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.m,
    paddingVertical: 13,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F2F5',
  },
  infoRowLast: { borderBottomWidth: 0 },
  infoLabel: { fontSize: FONT_SIZES.s, color: COLORS.gray },
  infoValue: { fontSize: FONT_SIZES.s, fontWeight: '500', color: COLORS.text, maxWidth: '55%', textAlign: 'right' },
  infoValueRow: { flexDirection: 'row', alignItems: 'center' },
  statusBadge: { paddingHorizontal: SPACING.m, paddingVertical: 4, borderRadius: BORDER_RADIUS.round },
  statusText: { fontSize: FONT_SIZES.xs, fontWeight: '600' },

  /* Bank card */
  bankCard: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.l,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  bankCardLabel: { fontSize: FONT_SIZES.xs, color: 'rgba(255,255,255,0.6)', marginBottom: 6 },
  bankCardNumber: { fontSize: FONT_SIZES.l, fontWeight: '700', color: COLORS.white, letterSpacing: 2 },
  bankCardEditBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardActions: { flexDirection: 'row', gap: SPACING.m, marginTop: SPACING.m },
  cardAction: { flex: 1 },

  /* Action rows */
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.m,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F2F5',
  },
  actionRowLast: { borderBottomWidth: 0 },
  actionIconWrap: {
    width: 36,
    height: 36,
    borderRadius: BORDER_RADIUS.m,
    backgroundColor: '#F4F6FA',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  actionLabel: { flex: 1, fontSize: FONT_SIZES.m, color: COLORS.text },

  /* Logout */
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.s,
    marginHorizontal: SPACING.l,
    marginTop: SPACING.l,
    paddingVertical: SPACING.m,
    borderRadius: BORDER_RADIUS.xl,
    borderWidth: 1.5,
    borderColor: COLORS.error,
    backgroundColor: COLORS.white,
  },
  logoutText: { fontSize: FONT_SIZES.m, fontWeight: '600', color: COLORS.error },

  /* City modal */
  cityModalHint: { fontSize: FONT_SIZES.s, color: COLORS.gray, marginBottom: SPACING.m, textAlign: 'center' },
  cityList: { maxHeight: 300, marginTop: SPACING.xs },
  cityItem: { marginBottom: SPACING.xs },

  /* Modals */
  modalText: { fontSize: FONT_SIZES.m, color: COLORS.text, lineHeight: 24 },
  referralBox: { backgroundColor: '#F4F6FA', borderRadius: BORDER_RADIUS.l, padding: SPACING.m, marginTop: SPACING.m },
  referralCode: { fontSize: FONT_SIZES.s, color: COLORS.primary, fontWeight: '600' },
});
