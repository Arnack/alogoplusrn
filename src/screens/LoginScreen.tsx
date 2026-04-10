import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, TouchableOpacity } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { useToast } from '../components/Toast';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { CustomModal } from '../components/Modal';
import { apiService } from '../services/api';
import { storage } from '../utils/storage';
import { registerForPushNotifications } from '../services/pushNotifications';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Entry: undefined;
  Login: undefined;
  Register: { phone: string };
  RegisterSelfEmployedQuestion: { phone: string };
  RegisterPersonalInfo: { phone: string; city: string };
  CitySelection: { phone: string };
  Dashboard: undefined;
};

type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Login'>;

interface LoginScreenProps {
  navigation: LoginScreenNavigationProp;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ navigation }) => {
  const [phone, setPhone] = useState('+7');
  const [innLast4, setInnLast4] = useState('');
  const [city, setCity] = useState('');
  const [loading, setLoading] = useState(false);
  const [cityModalVisible, setCityModalVisible] = useState(false);
  const [cities, setCities] = useState<string[]>([]);
  const [citySearch, setCitySearch] = useState('');
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    storage.getCity().then((c) => {
      if (c) setCity(c);
    });
    apiService.getCities().then((result: any) => {
      const data = result?.data ?? result;
      if (Array.isArray(data)) setCities(data.map((c: any) => c.name));
    }).catch(() => {});
  }, []);

  const filteredCities = cities.filter(c =>
    c.toLowerCase().includes(citySearch.toLowerCase())
  );

  const handleSelectCity = async (c: string) => {
    setCity(c);
    await storage.setCity(c);
    setCityModalVisible(false);
    setCitySearch('');
  };

  const formatPhone = (text: string): string => {
    let digits = text.replace(/\D/g, '');
    if (digits.startsWith('7') || digits.startsWith('8')) digits = digits.slice(1);
    digits = digits.slice(0, 10);
    let result = '+7';
    if (digits.length > 0) result += ' ' + digits.slice(0, 3);
    if (digits.length > 3) result += ' ' + digits.slice(3, 6);
    if (digits.length > 6) result += ' ' + digits.slice(6, 8);
    if (digits.length > 8) result += ' ' + digits.slice(8, 10);
    return result;
  };

  const handlePhoneChange = (text: string) => {
    setPhone(formatPhone(text));
  };

  const handleLogin = async () => {
    const cleanPhone = phone.replace(/\D/g, '');
    const cleanInnLast4 = innLast4.trim();

    if (cleanPhone.length !== 11) {
      error('Введите корректный номер телефона');
      return;
    }

    if (cleanInnLast4.length !== 4) {
      error('Введите последние 4 цифры ИНН');
      return;
    }

    if (!city) {
      error('Город не выбран. Пройдите регистрацию.');
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.loginPhone(`+${cleanPhone}`, cleanInnLast4, city);

      await storage.setToken(response.access_token);
      try {
        const me = await apiService.getMe();
        await storage.setUser(JSON.stringify(me));
      } catch {}

      registerForPushNotifications(); // fire-and-forget

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
    <SafeView style={styles.container}>
      <ScreenHeader title="Вход" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.subtitle}>Введите телефон и 4 цифры ИНН</Text>

        <View style={styles.content}>
          <Input
            label="Номер телефона"
            value={phone}
            onChangeText={handlePhoneChange}
            placeholder="+7 9XX XXX XX XX"
            keyboardType="phone-pad"
            maxLength={16}
          />

          <Input
            label="Последние 4 цифры ИНН"
            value={innLast4}
            onChangeText={(text) => setInnLast4(text.replace(/\D/g, '').slice(0, 4))}
            placeholder="1234"
            keyboardType="number-pad"
            maxLength={4}
            hint="Указан при регистрации"
          />

          <TouchableOpacity style={styles.cityPicker} onPress={() => setCityModalVisible(true)}>
            <Text style={styles.cityPickerLabel}>Город</Text>
            <Text style={[styles.cityPickerValue, !city && styles.cityPickerPlaceholder]}>
              {city || 'Выберите город'}
            </Text>
          </TouchableOpacity>

          <Button
            title="Войти"
            onPress={handleLogin}
            loading={loading}
            fullWidth
            size="large"
          />

          <Button
            title="Регистрация"
            onPress={() => navigation.navigate('Register', { phone: '' })}
            variant="outline"
            fullWidth
            style={styles.registerButton}
          />
        </View>
        </ScrollView>
      </KeyboardAvoidingView>
      <ToastContainer />

      <CustomModal
        visible={cityModalVisible}
        onClose={() => { setCityModalVisible(false); setCitySearch(''); }}
        title="Выберите город"
      >
        <Input
          label=""
          value={citySearch}
          onChangeText={setCitySearch}
          placeholder="Поиск города"
        />
        <ScrollView style={styles.cityList} nestedScrollEnabled showsVerticalScrollIndicator={false}>
          {filteredCities.map((c) => (
            <View key={c} style={styles.cityItem}>
              <Button
                title={c}
                onPress={() => handleSelectCity(c)}
                variant={city === c ? 'primary' : 'outline'}
                fullWidth
                size="medium"
              />
            </View>
          ))}
        </ScrollView>
      </CustomModal>
    </SafeView>
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
  subtitle: {
    fontSize: FONT_SIZES.l,
    color: COLORS.gray,
    marginBottom: SPACING.l,
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
  cityPicker: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.m,
    padding: SPACING.m,
    marginBottom: SPACING.m,
  },
  cityPickerLabel: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    marginBottom: 4,
  },
  cityPickerValue: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
  },
  cityPickerPlaceholder: {
    color: COLORS.gray,
  },
  cityList: {
    maxHeight: 300,
    marginTop: SPACING.s,
  },
  cityItem: {
    marginBottom: SPACING.xs,
  },
});
