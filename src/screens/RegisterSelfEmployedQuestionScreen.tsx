import React from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Image } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';

type RootStackParamList = {
  Entry: undefined;
  Login: undefined;
  Register: undefined;
  RegisterSelfEmployedQuestion: { phone: string };
  RegisterPersonalInfo: { phone: string; city: string };
  CitySelection: { phone: string };
  Dashboard: undefined;
};

type RegisterSelfEmployedQuestionProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'RegisterSelfEmployedQuestion'>;
  route: RouteProp<RootStackParamList, 'RegisterSelfEmployedQuestion'>;
};

export const RegisterSelfEmployedQuestionScreen: React.FC<RegisterSelfEmployedQuestionProps> = ({ navigation, route }) => {
  const { phone = '' } = route.params || {};

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>Как стать самозанятым</Text>
          <Text style={styles.subtitle}>Следуйте инструкции ниже</Text>
        </View>

        <View style={styles.card}>
          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>1</Text>
            </View>
            <Text style={styles.stepText}>Скачайте приложение «Мой налог»</Text>
          </View>

          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>2</Text>
            </View>
            <Text style={styles.stepText}>Нажмите «Стать самозанятым»</Text>
          </View>

          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>3</Text>
            </View>
            <Text style={styles.stepText}>Подтвердите номер телефона</Text>
          </View>

          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>4</Text>
            </View>
            <Text style={styles.stepText}>Введите паспортные данные</Text>
          </View>

          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>5</Text>
            </View>
            <Text style={styles.stepText}>Сделайте фото</Text>
          </View>

          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>6</Text>
            </View>
            <Text style={styles.stepText}>Подтвердите регистрацию</Text>
          </View>
        </View>

        <View style={styles.tipCard}>
          <Text style={styles.tipTitle}>💡 Подключите партнёра</Text>
          <Text style={styles.tipText}>
            Откройте «Мой налог» → «…» (три точки) → «Партнёры» → Найдите «Рабочие Руки» → «Разрешить доступ»
          </Text>
        </View>

        <Button
          title="Я стал самозанятым"
          onPress={() =>
            navigation.navigate('RegisterPersonalInfo', { phone, city: '' })
          }
          fullWidth
          size="large"
          style={styles.button}
        />

        <Button
          title="← Назад"
          onPress={() => navigation.goBack()}
          variant="outline"
          fullWidth
          size="medium"
        />
      </ScrollView>
    </KeyboardAvoidingView>
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
  header: {
    marginBottom: SPACING.l,
  },
  title: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: SPACING.xs,
  },
  subtitle: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    padding: SPACING.l,
    marginBottom: SPACING.l,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  step: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.m,
  },
  stepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  stepNumberText: {
    fontSize: FONT_SIZES.m,
    fontWeight: '700',
    color: COLORS.white,
  },
  stepText: {
    flex: 1,
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 22,
  },
  tipCard: {
    backgroundColor: '#f0f4ff',
    borderRadius: BORDER_RADIUS.l,
    padding: SPACING.l,
    marginBottom: SPACING.l,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  tipTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.s,
  },
  tipText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 22,
  },
  button: {
    marginBottom: SPACING.m,
  },
});
