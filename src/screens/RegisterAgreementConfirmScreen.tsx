import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import { storage } from '../utils/storage';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';

type RootStackParamList = {
  Entry: undefined;
  Login: undefined;
  Register: { phone: string };
  RegisterCity: { phone: string };
  RegisterLastName: { phone: string; city: string };
  RegisterInn: { phone: string; city: string; lastName: string; firstName: string; middleName: string };
  RegisterCard: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string };
  RegisterPhoneConfirm: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterAgreement: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterAgreementConfirm: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterSuccess: undefined;
  Dashboard: undefined;
};

type RegisterAgreementConfirmNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterAgreementConfirm'>;

type RegisterAgreementConfirmProps = {
  navigation: RegisterAgreementConfirmNavigationProp;
  route: RouteProp<RootStackParamList, 'RegisterAgreementConfirm'>;
};

export const RegisterAgreementConfirmScreen: React.FC<RegisterAgreementConfirmProps> = ({ navigation, route }) => {
  const params = route.params || {};
  const { phone = '', city = '', lastName = '', firstName = '', middleName = '', inn = '', card = '' } = params;
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const { error, success, ToastContainer } = useToast();

  const innLast4 = inn.slice(-4);

  const handleConfirm = async () => {
    if (pin.length !== 4) {
      error('Введите 4 последние цифры ИНН');
      return;
    }

    if (pin !== innLast4) {
      error('Неверный код. Введите последние 4 цифры вашего ИНН');
      return;
    }

    setLoading(true);
    try {
      // TODO: register user with backend API
      // const response = await apiService.register({...});
      // await storage.setToken(response.data.token);
      // await storage.setUser(JSON.stringify(response.data.user));

      await storage.setToken('temp_token');
      await storage.setUser(JSON.stringify({
        phone, city, lastName, firstName, middleName, inn, card,
      }));

      navigation.reset({
        index: 0,
        routes: [{ name: 'RegisterSuccess' }],
      });
    } catch (err: any) {
      error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Подтверждение подписи" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>Введите последние 4 цифры ИНН</Text>

          <View style={styles.content}>
            <Text style={styles.infoText}>
              Для подтверждения подписи договора введите последние 4 цифры вашего ИНН
            </Text>

            <Input
              label="4 цифры ИНН"
              value={pin}
              onChangeText={(text) => setPin(text.replace(/\D/g, '').slice(0, 4))}
              placeholder="••••"
              keyboardType="number-pad"
              maxLength={4}
            />

            <Button
              title="Подтвердить и завершить регистрацию"
              onPress={handleConfirm}
              loading={loading}
              fullWidth
              size="large"
            />
          </View>

          <View style={styles.buttonContainer}>
            <Button
              title="← Назад"
              onPress={() => navigation.goBack()}
              variant="outline"
              fullWidth
              style={styles.button}
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
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
    flexGrow: 1,
    padding: SPACING.l,
  },
  subtitle: {
    fontSize: FONT_SIZES.m,
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
  infoText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: SPACING.l,
    lineHeight: 22,
  },
  button: {
    marginTop: SPACING.s,
  },
  buttonContainer: {
    marginTop: SPACING.l,
  },
});
