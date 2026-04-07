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

type RegisterLastNameNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterLastName'>;

type RegisterLastNameProps = {
  navigation: RegisterLastNameNavigationProp;
  route: RouteProp<RootStackParamList, 'RegisterLastName'>;
};

export const RegisterLastNameScreen: React.FC<RegisterLastNameProps> = ({ navigation, route }) => {
  const { phone = '', city = '' } = route.params || {};
  const [lastName, setLastName] = useState('');
  const [firstName, setFirstName] = useState('');
  const [middleName, setMiddleName] = useState('');
  const [loading, setLoading] = useState(false);
  const { error, ToastContainer } = useToast();

  const handleContinue = () => {
    if (lastName.trim().length < 2) {
      error('Фамилия должна содержать минимум 2 символа');
      return;
    }
    if (firstName.trim().length < 2) {
      error('Имя должно содержать минимум 2 символа');
      return;
    }

    navigation.navigate('RegisterInn', {
      phone,
      city,
      lastName: lastName.trim(),
      firstName: firstName.trim(),
      middleName: middleName.trim(),
    });
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Личные данные" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>Шаг 1 из 5</Text>

          <View style={styles.content}>
            <Input
              label="Фамилия *"
              value={lastName}
              onChangeText={setLastName}
              placeholder="Иванов"
              autoCapitalize="words"
            />

            <Input
              label="Имя *"
              value={firstName}
              onChangeText={setFirstName}
              placeholder="Иван"
              autoCapitalize="words"
            />

            <Input
              label="Отчество (при наличии)"
              value={middleName}
              onChangeText={setMiddleName}
              placeholder="Иванович"
              autoCapitalize="words"
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
