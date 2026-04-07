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

type RegisterPhoneConfirmNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterPhoneConfirm'>;

type RegisterPhoneConfirmProps = {
  navigation: RegisterPhoneConfirmNavigationProp;
  route: RouteProp<RootStackParamList, 'RegisterPhoneConfirm'>;
};

export const RegisterPhoneConfirmScreen: React.FC<RegisterPhoneConfirmProps> = ({ navigation, route }) => {
  const params = route.params || {};
  const { phone = '', city = '', lastName = '', firstName = '', middleName = '', inn = '', card = '' } = params;
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const { error, success, ToastContainer } = useToast();

  const handleConfirm = async () => {
    if (code.length < 4) {
      error('Введите код подтверждения');
      return;
    }

    setLoading(true);
    try {
      // TODO: verify SMS code with backend
      // await apiService.verifySmsCode(phone, code);

      await storage.setCity(city);

      navigation.navigate('RegisterAgreement', {
        phone, city, lastName, firstName, middleName, inn, card,
      });
      success('Телефон подтверждён');
    } catch (err: any) {
      error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Подтверждение телефона" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>Шаг 5 из 5</Text>

          <View style={styles.content}>
            <Text style={styles.phoneText}>{phone}</Text>
            <Text style={styles.infoText}>
              Мы отправили SMS с кодом подтверждения на ваш номер телефона
            </Text>

            <Input
              label="Код из SMS"
              value={code}
              onChangeText={(text) => setCode(text.replace(/\D/g, '').slice(0, 6))}
              placeholder="Код"
              keyboardType="number-pad"
              maxLength={6}
            />

            <Button
              title="Подтвердить"
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
  phoneText: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: SPACING.s,
  },
  infoText: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    textAlign: 'center',
    marginBottom: SPACING.l,
  },
  button: {
    marginTop: SPACING.s,
  },
  buttonContainer: {
    marginTop: SPACING.l,
  },
});
