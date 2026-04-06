import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, TouchableOpacity, Linking } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import { storage } from '../utils/storage';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Entry: undefined;
  Login: undefined;
  Register: undefined;
  CitySelection: { phone: string };
  Dashboard: undefined;
};

type EntryScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Entry'>;

interface EntryScreenProps {
  navigation: EntryScreenNavigationProp;
}

export const EntryScreen: React.FC<EntryScreenProps> = ({ navigation }) => {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const { success, error, ToastContainer } = useToast();

  const formatPhone = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    const match = cleaned.match(/^(\d{0,1})(\d{0,3})(\d{0,3})(\d{0,2})(\d{0,2})$/);
    if (match) {
      let result = '+7';
      if (match[2]) result += ` ${match[2]}`;
      if (match[3]) result += ` ${match[3]}`;
      if (match[4]) result += ` ${match[4]}`;
      if (match[5]) result += ` ${match[5]}`;
      return result;
    }
    return text;
  };

  const handlePhoneChange = (text: string) => {
    const formatted = formatPhone(text);
    if (formatted.length <= 18) {
      setPhone(formatted);
    }
  };

  const checkUser = async () => {
    const cleanPhone = phone.replace(/\D/g, '');

    if (cleanPhone.length !== 11) {
      error('Введите корректный номер телефона');
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.checkUser(`+${cleanPhone}`, 'Не выбран');

      if (response.data.exists) {
        // User exists, go to login
        navigation.navigate('Login');
        success('Пользователь найден. Введите ИНН для входа.');
      } else {
        // User doesn't exist, go to registration
        navigation.navigate('CitySelection', { phone: `+${cleanPhone}` });
      }
    } catch (err: any) {
      error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>AlgoritmPlus</Text>
          <Text style={styles.subtitle}>Платформа для самозанятых</Text>
        </View>

        <View style={styles.content}>
          <Text style={styles.label}>Номер телефона</Text>
          <Input
            value={phone}
            onChangeText={handlePhoneChange}
            placeholder="+7 ___ ___ __ __"
            keyboardType="phone-pad"
            maxLength={18}
          />

          <Button
            title="Продолжить"
            onPress={checkUser}
            loading={loading}
            fullWidth
            size="large"
          />

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>или</Text>
            <View style={styles.dividerLine} />
          </View>

          <TouchableOpacity
            style={styles.loginLink}
            onPress={() => navigation.navigate('Login')}
          >
            <Text style={styles.loginLinkText}>Уже есть аккаунт? Войти</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Продолжая, вы соглашаетесь с{'\n'}
            <Text style={styles.footerLink} onPress={() => Linking.openURL('https://algoritmplus.online/user-agreement')}>
              Пользовательским соглашением
            </Text>
            {' '}и{' '}
            <Text style={styles.footerLink} onPress={() => Linking.openURL('https://algoritmplus.online/docs/privacy-policy')}>
              Политикой конфиденциальности
            </Text>
          </Text>
        </View>
      </ScrollView>
      <ToastContainer />
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: SPACING.l,
  },
  header: {
    alignItems: 'center',
    marginBottom: SPACING.xxl,
  },
  title: {
    fontSize: FONT_SIZES.xxxl,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: SPACING.xs,
  },
  subtitle: {
    fontSize: FONT_SIZES.l,
    color: COLORS.gray,
  },
  content: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.l,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  label: {
    fontSize: FONT_SIZES.m,
    fontWeight: '500',
    color: COLORS.text,
    marginBottom: SPACING.s,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: SPACING.l,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.border,
  },
  dividerText: {
    marginHorizontal: SPACING.m,
    color: COLORS.gray,
    fontSize: FONT_SIZES.s,
  },
  loginLink: {
    alignItems: 'center',
    paddingVertical: SPACING.m,
  },
  loginLinkText: {
    color: COLORS.primary,
    fontSize: FONT_SIZES.m,
    fontWeight: '500',
  },
  footer: {
    marginTop: SPACING.xl,
    alignItems: 'center',
  },
  footerText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    textAlign: 'center',
  },
  footerLink: {
    color: COLORS.primary,
    textDecorationLine: 'underline',
  },
});
