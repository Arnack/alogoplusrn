import React, { useEffect } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Linking } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { SafeView } from '../components/SafeView';
import { storage } from '../utils/storage';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Entry: undefined;
  Login: undefined;
  Register: { phone: string; city: string };
  RegisterSelfEmployedQuestion: { phone: string };
  RegisterPersonalInfo: { phone: string; city: string };
  CitySelection: { phone: string };
  Dashboard: undefined;
};


type EntryScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Entry'>;

interface EntryScreenProps {
  navigation: EntryScreenNavigationProp;
}

export const EntryScreen: React.FC<EntryScreenProps> = ({ navigation }) => {
  useEffect(() => {
    storage.getToken().then((token) => {
      if (token) navigation.replace('Dashboard');
    });
  }, []);

  return (
    <SafeView style={styles.container}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>Алгоритм Плюс</Text>
          <Text style={styles.subtitle}>Платформа для самозанятых</Text>
        </View>

        <View style={styles.content}>
          <Button
            title="Войти"
            onPress={() => navigation.navigate('Login')}
            fullWidth
            size="large"
          />

          <View style={styles.divider} />

          <Button
            title="Регистрация"
            onPress={() => navigation.navigate('Register', { phone: '', city: '' })}
            variant="outline"
            fullWidth
            size="large"
          />
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Продолжая, вы соглашаетесь с{'\n'}
            <Text style={styles.footerLink} onPress={() => Linking.openURL('https://algoritmplus.online/user-agreement')}>
              Пользовательским соглашением
            </Text>
            {' '}и{' '}
            <Text style={styles.footerLink} onPress={() => Linking.openURL('https://algoritmplus.online/docs/privacy-policy')}>
              Политикой конфиденциальности
            </Text>
          </Text>
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
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginVertical: SPACING.m,
  },
  footer: {
    marginTop: SPACING.xl,
    alignItems: 'center',
  },
  footerText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    textAlign: 'center',
  },
  footerLink: {
    color: COLORS.primary,
    textDecorationLine: 'underline',
  },
});
