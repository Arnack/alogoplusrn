import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { CustomModal } from '../components/Modal';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import { storage } from '../utils/storage';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';

type RegisterScreenProps = {
  navigation: NativeStackNavigationProp<any, 'Register'>;
  route: RouteProp<any, 'Register'>;
};

export const RegisterScreen: React.FC<RegisterScreenProps> = ({ navigation, route }) => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    middleName: '',
    birthday: '',
    inn: '',
    bankCard: '',
  });
  const [isSelfEmployed, setIsSelfEmployed] = useState(true);
  const [loading, setLoading] = useState(false);
  const [showSMZInfo, setShowSMZInfo] = useState(false);
  const { success, error, ToastContainer } = useToast();

  const { phone = '', cityId = 0, cityName = '' } = route.params || {};

  const formatBirthday = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    const match = cleaned.match(/^(\d{0,2})(\d{0,2})(\d{0,4})$/);
    if (match) {
      let result = '';
      if (match[1]) result += match[1];
      if (match[2]) result += `.${match[2]}`;
      if (match[3]) result += `.${match[3]}`;
      return result;
    }
    return text;
  };

  const handleBirthdayChange = (text: string) => {
    const formatted = formatBirthday(text);
    if (formatted.length <= 10) {
      setFormData({ ...formData, birthday: formatted });
    }
  };

  const formatCardNumber = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    const formatted = cleaned.replace(/(\d{4})/g, '$1 ').trim();
    return formatted;
  };

  const handleCardChange = (text: string) => {
    const formatted = formatCardNumber(text);
    if (formatted.length <= 23) {
      setFormData({ ...formData, bankCard: formatted });
    }
  };

  const validateForm = () => {
    if (!formData.lastName.trim()) {
      error('Введите фамилию');
      return false;
    }
    if (!formData.firstName.trim()) {
      error('Введите имя');
      return false;
    }
    if (!formData.birthday || formData.birthday.length !== 10) {
      error('Введите дату рождения');
      return false;
    }
    if (!formData.inn || formData.inn.length !== 12) {
      error('ИНН должен содержать 12 цифр');
      return false;
    }
    if (!formData.bankCard || formData.bankCard.replace(/\s/g, '').length < 16) {
      error('Введите корректный номер карты');
      return false;
    }
    return true;
  };

  const handleRegister = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      // Here we would call the registration endpoint
      // The actual registration flow involves SMS verification and contract signing
      // For now, we'll simulate a simplified flow
      
      // await apiService.register({
      //   phone,
      //   firstName: formData.firstName,
      //   lastName: formData.lastName,
      //   middleName: formData.middleName,
      //   birthday: formData.birthday,
      //   inn: formData.inn,
      //   city: cityName,
      //   bankCard: formData.bankCard.replace(/\s/g, ''),
      // });

      // Simulated success
      await storage.setCity(cityName);
      success('Регистрация завершена. Переходим на главную.');
      navigation.reset({
        index: 0,
        routes: [{ name: 'Dashboard' }],
      });
    } catch (err: any) {
      error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>Регистрация</Text>
          <Text style={styles.subtitle}>{phone} · {cityName}</Text>
        </View>

        <View style={styles.content}>
          <Input
            label="Фамилия"
            value={formData.lastName}
            onChangeText={(text) => setFormData({ ...formData, lastName: text })}
            placeholder="Иванов"
            autoCapitalize="words"
          />

          <Input
            label="Имя"
            value={formData.firstName}
            onChangeText={(text) => setFormData({ ...formData, firstName: text })}
            placeholder="Иван"
            autoCapitalize="words"
          />

          <Input
            label="Отчество (если есть)"
            value={formData.middleName}
            onChangeText={(text) => setFormData({ ...formData, middleName: text })}
            placeholder="Иванович"
            autoCapitalize="words"
          />

          <Input
            label="Дата рождения"
            value={formData.birthday}
            onChangeText={handleBirthdayChange}
            placeholder="ДД.ММ.ГГГГ"
            keyboardType="number-pad"
            maxLength={10}
          />

          <Input
            label="ИНН"
            value={formData.inn}
            onChangeText={(text) => setFormData({ ...formData, inn: text.replace(/\D/g, '') })}
            placeholder="12 цифр"
            keyboardType="number-pad"
            maxLength={12}
          />

          <Input
            label="Номер банковской карты"
            value={formData.bankCard}
            onChangeText={handleCardChange}
            placeholder="0000 0000 0000 0000"
            keyboardType="number-pad"
            maxLength={23}
            hint="Для вывода средств"
          />

          {!isSelfEmployed && (
            <Button
              title="Как стать самозанятым"
              onPress={() => setShowSMZInfo(true)}
              variant="outline"
              fullWidth
              style={styles.smzInfoButton}
            />
          )}

          <Button
            title="Зарегистрироваться"
            onPress={handleRegister}
            loading={loading}
            fullWidth
            size="large"
          />
        </View>

        <CustomModal
          visible={showSMZInfo}
          onClose={() => setShowSMZInfo(false)}
          title="Как стать самозанятым"
        >
          <Text style={styles.modalText}>
            1. Скачайте приложение "Мой налог"{'\n\n'}
            2. Зарегистрируйтесь через Госуслуги или по ИНН{'\n\n'}
            3. После регистрации вернитесь и продолжите оформление
          </Text>
          <Button
            title="Я стал самозанятым"
            onPress={() => {
              setIsSelfEmployed(true);
              setShowSMZInfo(false);
            }}
            fullWidth
            style={styles.modalButton}
          />
        </CustomModal>
      </ScrollView>
      <ToastContainer />
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
  smzInfoButton: {
    marginBottom: SPACING.m,
  },
  modalText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 24,
    marginBottom: SPACING.l,
  },
  modalButton: {
    marginTop: SPACING.m,
  },
});
