import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { LoadingScreen } from '../components/Loading';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import { storage } from '../utils/storage';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Profile: undefined;
  Login: undefined;
  RemoveAccount: undefined;
};

type RemoveAccountScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RemoveAccount'>;

interface RemoveAccountScreenProps {
  navigation: RemoveAccountScreenNavigationProp;
}

export const RemoveAccountScreen: React.FC<RemoveAccountScreenProps> = ({ navigation }) => {
  const [notice, setNotice] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    loadNotice();
  }, []);

  const loadNotice = async () => {
    try {
      const res = await apiService.getDataErasureNotice();
      const message = res?.message || res?.data?.message || '';
      setNotice(message);
    } catch {
      setNotice('Не удалось загрузить информацию об удалении данных.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!confirmed) {
      error('Подтвердите удаление данных');
      return;
    }

    setDeleting(true);
    try {
      const res = await apiService.erasePersonalData();
      const message = res?.message || res?.data?.message || '';
      
      // Clear all local storage
      await storage.clearAll();
      
      success(message || 'Данные успешно удалены');
      
      // Navigate to login after a short delay
      setTimeout(() => {
        navigation.reset({
          index: 0,
          routes: [{ name: 'Login' }],
        });
      }, 1500);
    } catch (err: any) {
      error(err.message || 'Ошибка при удалении данных');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <LoadingScreen text="Загрузка..." />;
  }

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Удалить данные" onBack={() => navigation.goBack()} />

      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        {/* Warning Icon */}
        <View style={styles.warningIcon}>
          <Ionicons name="warning" size={48} color={COLORS.error} />
        </View>

        {/* Notice Card */}
        <View style={styles.noticeCard}>
          <Text style={styles.noticeTitle}>Внимание</Text>
          <Text style={styles.noticeText}>{notice}</Text>
        </View>

        {/* What will be deleted */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Будет удалено:</Text>
          <View style={styles.listCard}>
            <View style={styles.listItem}>
              <Ionicons name="close-circle" size={18} color={COLORS.error} />
              <Text style={styles.listItemText}>Фамилия, Имя, Отчество</Text>
            </View>
            <View style={styles.listItem}>
              <Ionicons name="close-circle" size={18} color={COLORS.error} />
              <Text style={styles.listItemText}>Номер телефона</Text>
            </View>
            <View style={styles.listItem}>
              <Ionicons name="close-circle" size={18} color={COLORS.error} />
              <Text style={styles.listItemText}>Telegram ID</Text>
            </View>
          </View>
        </View>

        {/* What will be retained */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Будет сохранено:</Text>
          <View style={styles.listCard}>
            <View style={styles.listItem}>
              <Ionicons name="checkmark-circle" size={18} color="#27AE60" />
              <Text style={styles.listItemText}>История заказов</Text>
            </View>
            <View style={styles.listItem}>
              <Ionicons name="checkmark-circle" size={18} color="#27AE60" />
              <Text style={styles.listItemText}>Рейтинг</Text>
            </View>
          </View>
        </View>

        {/* Confirmation Checkbox */}
        <TouchableOpacity
          style={styles.checkboxRow}
          onPress={() => setConfirmed(!confirmed)}
          activeOpacity={0.7}
        >
          <View style={[styles.checkbox, confirmed && styles.checkboxChecked]}>
            {confirmed && <Ionicons name="checkmark" size={16} color={COLORS.white} />}
          </View>
          <Text style={styles.checkboxLabel}>
            Я понимаю, что мои данные будут удалены
          </Text>
        </TouchableOpacity>

        {/* Delete Button */}
        <View style={styles.buttonContainer}>
          <Button
            title={deleting ? 'Удаление...' : 'Удалить аккаунт'}
            onPress={handleDeleteAccount}
            variant="danger"
            fullWidth
            disabled={!confirmed || deleting}
          />
        </View>

        <View style={{ height: SPACING.xl }} />
      </ScrollView>

      <ToastContainer />
    </SafeView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scroll: { paddingBottom: SPACING.xl, paddingHorizontal: SPACING.l, paddingTop: SPACING.l },

  /* Warning Icon */
  warningIcon: {
    alignItems: 'center',
    marginBottom: SPACING.l,
  },

  /* Notice Card */
  noticeCard: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.l,
    marginBottom: SPACING.l,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  noticeTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '700',
    color: COLORS.error,
    marginBottom: SPACING.m,
  },
  noticeText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 22,
  },

  /* Section */
  section: { marginBottom: SPACING.l },
  sectionTitle: {
    fontSize: FONT_SIZES.s,
    fontWeight: '600',
    color: COLORS.gray,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: SPACING.s,
  },
  listCard: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  listItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.m,
    paddingVertical: SPACING.m,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F2F5',
    gap: SPACING.m,
  },
  listItemText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    flex: 1,
  },

  /* Checkbox */
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.l,
    gap: SPACING.m,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: COLORS.gray,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxChecked: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  checkboxLabel: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    flex: 1,
  },

  /* Button */
  buttonContainer: {
    marginTop: SPACING.m,
  },
});
