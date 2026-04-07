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

type RegisterInnNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterInn'>;

type RegisterInnProps = {
  navigation: RegisterInnNavigationProp;
  route: RouteProp<RootStackParamList, 'RegisterInn'>;
};

export const RegisterInnScreen: React.FC<RegisterInnProps> = ({ navigation, route }) => {
  const params = route.params || {};
  const { phone = '', city = '', lastName = '', firstName = '', middleName = '' } = params;
  const [inn, setInn] = useState('');
  const [loading, setLoading] = useState(false);
  const { error, ToastContainer } = useToast();

  const handleContinue = () => {
    if (inn.length !== 12) {
      error('ИНН должен содержать 12 цифр');
      return;
    }

    navigation.navigate('RegisterCard', {
      phone, city, lastName, firstName, middleName, inn,
    });
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="ИНН" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>Шаг 2 из 5</Text>

          <View style={styles.content}>
            <Input
              label="ИНН *"
              value={inn}
              onChangeText={(text) => setInn(text.replace(/\D/g, '').slice(0, 12))}
              placeholder="12 цифр"
              keyboardType="number-pad"
              maxLength={12}
              hint="Ваш идентификационный номер налогоплательщика"
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
