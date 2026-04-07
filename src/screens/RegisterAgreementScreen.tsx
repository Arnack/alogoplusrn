import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Linking } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
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

type RegisterAgreementNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterAgreement'>;

type RegisterAgreementProps = {
  navigation: RegisterAgreementNavigationProp;
  route: RouteProp<RootStackParamList, 'RegisterAgreement'>;
};

export const RegisterAgreementScreen: React.FC<RegisterAgreementProps> = ({ navigation, route }) => {
  const params = route.params || {};
  const { phone = '', city = '', lastName = '', firstName = '', middleName = '', inn = '', card = '' } = params;
  const [loading, setLoading] = useState(false);

  const handleSign = () => {
    navigation.navigate('RegisterAgreementConfirm', {
      phone, city, lastName, firstName, middleName, inn, card,
    });
  };

  const fullName = `${lastName} ${firstName}${middleName ? ` ${middleName}` : ''}`;

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Подписание договора" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>Шаг 5 из 5</Text>

          <View style={styles.content}>
            <View style={styles.agreementCard}>
              <Text style={styles.agreementTitle}>Договор оферты</Text>
              <Text style={styles.agreementText}>
                Настоящим вы подтверждаете своё согласие с условиями оказания услуг платформой AlgoritmPlus.
              </Text>
              <Text style={styles.userName}>{fullName}</Text>
              <Text style={styles.userDetail}>ИНН: {inn}</Text>
              <Text style={styles.userDetail}>Город: {city}</Text>
            </View>

            <View style={styles.linksCard}>
              <Text
                style={styles.link}
                onPress={() => Linking.openURL('https://algoritmplus.online/user-agreement')}
              >
                📄 Пользовательское соглашение
              </Text>
              <Text
                style={styles.link}
                onPress={() => Linking.openURL('https://algoritmplus.online/docs/privacy-policy')}
              >
                📄 Политика конфиденциальности
              </Text>
            </View>

            <Button
              title="Подписать договор"
              onPress={handleSign}
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
  agreementCard: {
    marginBottom: SPACING.l,
    paddingBottom: SPACING.l,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  agreementTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.s,
  },
  agreementText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 22,
    marginBottom: SPACING.m,
  },
  userName: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.xs,
  },
  userDetail: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
    marginBottom: SPACING.xs,
  },
  linksCard: {
    marginBottom: SPACING.l,
  },
  link: {
    fontSize: FONT_SIZES.m,
    color: COLORS.primary,
    textDecorationLine: 'underline',
    paddingVertical: SPACING.s,
  },
  button: {
    marginTop: SPACING.s,
  },
  buttonContainer: {
    marginTop: SPACING.l,
  },
});
