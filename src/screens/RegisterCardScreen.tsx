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

type RegisterCardNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterCard'>;

type RegisterCardProps = {
  navigation: RegisterCardNavigationProp;
  route: RouteProp<RootStackParamList, 'RegisterCard'>;
};

const luhnCheck = (cardNumber: string): boolean => {
  const digits = cardNumber.replace(/\D/g, '');
  if (digits.length < 13 || digits.length > 19) return false;

  let sum = 0;
  let isEven = false;

  for (let i = digits.length - 1; i >= 0; i--) {
    let digit = parseInt(digits[i], 10);

    if (isEven) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }

    sum += digit;
    isEven = !isEven;
  }

  return sum % 10 === 0;
};

export const RegisterCardScreen: React.FC<RegisterCardProps> = ({ navigation, route }) => {
  const params = route.params || {};
  const { phone = '', city = '', lastName = '', firstName = '', middleName = '', inn = '' } = params;
  const [card, setCard] = useState('');
  const [loading, setLoading] = useState(false);
  const { error, success, ToastContainer } = useToast();

  const formatCardNumber = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    const formatted = cleaned.replace(/(\d{4})/g, '$1 ').trim();
    return formatted;
  };

  const handleCardChange = (text: string) => {
    const formatted = formatCardNumber(text);
    if (formatted.length <= 23) {
      setCard(formatted);
    }
  };

  const handleContinue = () => {
    const cardDigits = card.replace(/\D/g, '');
    if (cardDigits.length < 16 || cardDigits.length > 19) {
      error('Введите корректный номер карты (16-19 цифр)');
      return;
    }
    if (!luhnCheck(cardDigits)) {
      error('Некорректный номер карты');
      return;
    }

    navigation.navigate('RegisterPhoneConfirm', {
      phone, city, lastName, firstName, middleName, inn, card: cardDigits,
    });
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Банковская карта" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>Шаг 3 из 5</Text>

          <View style={styles.content}>
            <Input
              label="Номер карты *"
              value={card}
              onChangeText={handleCardChange}
              placeholder="0000 0000 0000 0000"
              keyboardType="number-pad"
              maxLength={23}
              hint="Для вывода средств. Минимальная сумма вывода — 2600₽"
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
