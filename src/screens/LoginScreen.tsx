import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
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

type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Login'>;

interface LoginScreenProps {
  navigation: LoginScreenNavigationProp;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ navigation }) => {
  const [phone, setPhone] = useState('');
  const [inn, setInn] = useState('');
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

  const handleLogin = async () => {
    const cleanPhone = phone.replace(/\D/g, '');
    const cleanInn = inn.trim();

    if (cleanPhone.length !== 11) {
      error('Введите корректный номер телефона');
      return;
    }

    if (cleanInn.length !== 12) {
      error('ИНН должен содержать 12 цифр');
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.loginPhone(`+${cleanPhone}`, cleanInn);
      
      await storage.setToken(response.data.token);
      await storage.setUser(JSON.stringify(response.data.user));
      
      success('Вы успешно вошли');
      navigation.reset({
        index: 0,
        routes: [{ name: 'Dashboard' }],
      });
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
          <Text style={styles.title}>Вход</Text>
          <Text style={styles.subtitle}>Введите телефон и ИНН</Text>
        </View>

        <View style={styles.content}>
          <Input
            label="Номер телефона"
            value={phone}
            onChangeText={handlePhoneChange}
            placeholder="+7 ___ ___ __ __"
            keyboardType="phone-pad"
            maxLength={18}
          />

          <Input
            label="ИНН"
            value={inn}
            onChangeText={setInn}
            placeholder="12 цифр ИНН"
            keyboardType="number-pad"
            maxLength={12}
            hint="ИНН указан при регистрации"
          />

          <Button
            title="Войти"
            onPress={handleLogin}
            loading={loading}
            fullWidth
            size="large"
          />

          <Button
            title="Регистрация"
            onPress={() => navigation.navigate('Entry')}
            variant="outline"
            fullWidth
            style={styles.registerButton}
          />
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
  registerButton: {
    marginTop: SPACING.m,
  },
});
