import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';

type RootStackParamList = {
  Entry: undefined;
  Login: undefined;
  Register: { phone: string };
  RegisterLastName: { phone: string; city: string };
  RegisterInn: { phone: string; city: string; lastName: string; firstName: string; middleName: string };
  RegisterCard: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string };
  RegisterPhone: { city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterPhoneConfirm: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterAgreement: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterSuccess: undefined;
  Dashboard: undefined;
};

type RegisterPhoneNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterPhone'>;

type RegisterPhoneProps = {
  navigation: RegisterPhoneNavigationProp;
  route: RouteProp<RootStackParamList, 'RegisterPhone'>;
};

export const RegisterPhoneScreen: React.FC<RegisterPhoneProps> = ({ navigation, route }) => {
  const { city = '', lastName = '', firstName = '', middleName = '', inn = '', card = '' } = route.params || {};
  const [phone, setPhone] = useState('+7');
  const [loading, setLoading] = useState(false);
  const { error, ToastContainer } = useToast();

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

  const handleContinue = () => {
    const digits = phone.replace(/\D/g, '');
    if (digits.length !== 11) {
      error('Введите корректный номер телефона');
      return;
    }
    navigation.navigate('RegisterPhoneConfirm', {
      phone: `+${digits}`,
      city, lastName, firstName, middleName, inn, card,
    });
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Номер телефона" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>Шаг 4 из 5</Text>

          <View style={styles.content}>
            <Input
              label="Номер телефона *"
              value={phone}
              onChangeText={handlePhoneChange}
              placeholder="+7 9XX XXX XX XX"
              keyboardType="phone-pad"
              maxLength={16}
              hint="На этот номер придёт SMS с кодом"
            />
          </View>

          <View style={styles.buttonContainer}>
            <Button
              title="Далее →"
              onPress={handleContinue}
              loading={loading}
              fullWidth
              size="large"
            />

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
  button: {
    marginTop: SPACING.s,
  },
  buttonContainer: {
    marginTop: SPACING.l,
  },
});
