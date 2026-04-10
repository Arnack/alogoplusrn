import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { SafeView } from '../components/SafeView';
import { registerForPushNotifications } from '../services/pushNotifications';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  RegisterSuccess: undefined;
  Dashboard: undefined;
};

type RegisterSuccessNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterSuccess'>;

export const RegisterSuccessScreen: React.FC<{ navigation: RegisterSuccessNavigationProp }> = ({ navigation }) => {
  const handleGoToDashboard = async () => {
    registerForPushNotifications(); // fire-and-forget
    navigation.reset({
      index: 0,
      routes: [{ name: 'Dashboard' }],
    });
  };

  return (
    <SafeView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.content}>
          <View style={styles.iconContainer}>
            <Text style={styles.icon}>✅</Text>
          </View>

          <Text style={styles.title}>Регистрация завершена!</Text>
          <Text style={styles.subtitle}>
            Добро пожаловать в Алгоритм Плюс.{'\n'}
            Ваш аккаунт успешно создан.
          </Text>

          <Button
            title="Перейти на главную"
            onPress={handleGoToDashboard}
            fullWidth
            size="large"
          />
        </View>
      </ScrollView>
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
  content: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.xl,
    alignItems: 'center',
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#e8f5e9',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.l,
  },
  icon: {
    fontSize: 40,
  },
  title: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: SPACING.s,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: FONT_SIZES.l,
    color: COLORS.gray,
    textAlign: 'center',
    marginBottom: SPACING.xl,
    lineHeight: 24,
  },
});
