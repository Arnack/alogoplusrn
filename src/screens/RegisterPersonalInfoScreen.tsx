import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Linking, TouchableOpacity } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import { storage } from '../utils/storage';
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

type RegisterPersonalInfoProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'RegisterPersonalInfo'>;
  route: RouteProp<RootStackParamList, 'RegisterPersonalInfo'>;
};

export const RegisterPersonalInfoScreen: React.FC<RegisterPersonalInfoProps> = ({ navigation, route }) => {
  const { phone = '', city = '' } = route.params || {};

  const [formData, setFormData] = useState({
    lastName: '',
    firstName: '',
    middleName: '',
    birthday: '',
    gender: '',
    passportSeries: '',
    passportNumber: '',
    passportDate: '',
    passportDeptCode: '',
    passportIssuedBy: '',
    inn: '',
    bankCard: '',
  });
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const { success, error, warning, ToastContainer } = useToast();

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

  const formatCardNumber = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    const formatted = cleaned.replace(/(\d{4})/g, '$1 ').trim();
    return formatted;
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

  const handleBirthdayChange = (text: string) => {
    const formatted = formatBirthday(text);
    if (formatted.length <= 10) {
      setFormData({ ...formData, birthday: formatted });
    }
  };

  const handleCardChange = (text: string) => {
    const formatted = formatCardNumber(text);
    if (formatted.length <= 23) {
      setFormData({ ...formData, bankCard: formatted });
    }
  };

  const validateStep = (): boolean => {
    switch (step) {
      case 1: // ФИО
        if (formData.lastName.trim().length < 2) {
          error('Фамилия должна содержать минимум 2 символа');
          return false;
        }
        if (formData.firstName.trim().length < 2) {
          error('Имя должно содержать минимум 2 символа');
          return false;
        }
        return true;
      case 2: // Паспортные данные
        if (!formData.birthday || formData.birthday.length !== 10) {
          error('Введите дату рождения в формате ДД.ММ.ГГГГ');
          return false;
        }
        if (!formData.gender) {
          error('Выберите пол');
          return false;
        }
        if (formData.passportSeries.length !== 4) {
          error('Серия паспорта должна содержать 4 цифры');
          return false;
        }
        if (formData.passportNumber.length !== 6) {
          error('Номер паспорта должен содержать 6 цифр');
          return false;
        }
        if (!formData.passportDate || formData.passportDate.length !== 10) {
          error('Введите дату выдачи паспорта в формате ДД.ММ.ГГГГ');
          return false;
        }
        if (formData.passportDeptCode.replace(/\D/g, '').length !== 6) {
          error('Код подразделения должен содержать 6 цифр');
          return false;
        }
        if (formData.passportIssuedBy.trim().length < 5) {
          error('Кем выдан паспорт — минимум 5 символов');
          return false;
        }
        return true;
      case 3: // ИНН и карта
        if (formData.inn.length !== 12) {
          error('ИНН должен содержать 12 цифр');
          return false;
        }
        const cardDigits = formData.bankCard.replace(/\D/g, '');
        if (cardDigits.length < 16 || cardDigits.length > 19) {
          error('Введите корректный номер карты');
          return false;
        }
        if (!luhnCheck(cardDigits)) {
          error('Некорректный номер карты');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const nextStep = () => {
    if (!validateStep()) return;
    setStep(step + 1);
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  const handleRegister = async () => {
    if (!validateStep()) return;

    setLoading(true);
    try {
      // The actual registration flow:
      // 1. Create worker in partner API
      // 2. Check FNS/SMZ status
      // 3. Create user in local DB
      // 4. Sign contracts

      // For now, simulate registration
      await storage.setCity(city || 'Не указан');

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

  const stepTitle = (): string => {
    switch (step) {
      case 1: return 'Личные данные';
      case 2: return 'Паспортные данные';
      case 3: return 'ИНН и банковская карта';
      default: return '';
    }
  };

  const stepSubtitle = (): string => {
    switch (step) {
      case 1: return 'Шаг 1 из 3';
      case 2: return 'Шаг 2 из 3';
      case 3: return 'Шаг 3 из 3';
      default: return '';
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>{stepTitle()}</Text>
          <Text style={styles.subtitle}>{stepSubtitle()}</Text>
          {phone && <Text style={styles.phone}>{phone}</Text>}
        </View>

        {/* Progress indicator */}
        <View style={styles.progressContainer}>
          {[1, 2, 3].map((s) => (
            <View
              key={s}
              style={[
                styles.progressDot,
                s <= step ? styles.progressDotActive : styles.progressDotInactive,
              ]}
            />
          ))}
        </View>

        <View style={styles.content}>
          {step === 1 && (
            <>
              <Input
                label="Фамилия *"
                value={formData.lastName}
                onChangeText={(text) => setFormData({ ...formData, lastName: text })}
                placeholder="Иванов"
                autoCapitalize="words"
              />

              <Input
                label="Имя *"
                value={formData.firstName}
                onChangeText={(text) => setFormData({ ...formData, firstName: text })}
                placeholder="Иван"
                autoCapitalize="words"
              />

              <Input
                label="Отчество (необязательно)"
                value={formData.middleName}
                onChangeText={(text) => setFormData({ ...formData, middleName: text })}
                placeholder="Иванович"
                autoCapitalize="words"
              />
            </>
          )}

          {step === 2 && (
            <>
              <Input
                label="Дата рождения *"
                value={formData.birthday}
                onChangeText={handleBirthdayChange}
                placeholder="ДД.ММ.ГГГГ"
                keyboardType="number-pad"
                maxLength={10}
              />

              <View style={styles.genderContainer}>
                <Text style={styles.genderLabel}>Пол *</Text>
                <View style={styles.genderButtons}>
                  <TouchableOpacity
                    style={[
                      styles.genderButton,
                      formData.gender === 'M' && styles.genderButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, gender: 'M' })}
                  >
                    <Text
                      style={[
                        styles.genderButtonText,
                        formData.gender === 'M' && styles.genderButtonTextActive,
                      ]}
                    >
                      Мужской
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[
                      styles.genderButton,
                      formData.gender === 'F' && styles.genderButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, gender: 'F' })}
                  >
                    <Text
                      style={[
                        styles.genderButtonText,
                        formData.gender === 'F' && styles.genderButtonTextActive,
                      ]}
                    >
                      Женский
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>

              <Input
                label="Серия паспорта *"
                value={formData.passportSeries}
                onChangeText={(text) => setFormData({ ...formData, passportSeries: text.replace(/\D/g, '').slice(0, 4) })}
                placeholder="4510"
                keyboardType="number-pad"
                maxLength={4}
              />

              <Input
                label="Номер паспорта *"
                value={formData.passportNumber}
                onChangeText={(text) => setFormData({ ...formData, passportNumber: text.replace(/\D/g, '').slice(0, 6) })}
                placeholder="123456"
                keyboardType="number-pad"
                maxLength={6}
              />

              <Input
                label="Дата выдачи паспорта *"
                value={formData.passportDate}
                onChangeText={handleBirthdayChange}
                placeholder="ДД.ММ.ГГГГ"
                keyboardType="number-pad"
                maxLength={10}
              />

              <Input
                label="Код подразделения *"
                value={formData.passportDeptCode}
                onChangeText={(text) => {
                  const cleaned = text.replace(/\D/g, '').slice(0, 6);
                  setFormData({ ...formData, passportDeptCode: cleaned });
                }}
                placeholder="000-000"
                keyboardType="number-pad"
                maxLength={6}
              />

              <Input
                label="Кем выдан паспорт *"
                value={formData.passportIssuedBy}
                onChangeText={(text) => setFormData({ ...formData, passportIssuedBy: text })}
                placeholder="Отделом УФМС России"
                autoCapitalize="sentences"
                multiline
                numberOfLines={2}
              />
            </>
          )}

          {step === 3 && (
            <>
              <Input
                label="ИНН *"
                value={formData.inn}
                onChangeText={(text) => setFormData({ ...formData, inn: text.replace(/\D/g, '').slice(0, 12) })}
                placeholder="12 цифр"
                keyboardType="number-pad"
                maxLength={12}
              />

              <Input
                label="Номер банковской карты *"
                value={formData.bankCard}
                onChangeText={handleCardChange}
                placeholder="0000 0000 0000 0000"
                keyboardType="number-pad"
                maxLength={23}
                hint="Для вывода средств"
              />
            </>
          )}
        </View>

        <View style={styles.buttonContainer}>
          {step > 1 && (
            <Button
              title="← Назад"
              onPress={prevStep}
              variant="outline"
              fullWidth
              style={styles.button}
            />
          )}

          {step < 3 ? (
            <Button
              title="Далее →"
              onPress={nextStep}
              fullWidth
              size="large"
            />
          ) : (
            <Button
              title="Зарегистрироваться"
              onPress={handleRegister}
              loading={loading}
              fullWidth
              size="large"
            />
          )}
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
    marginBottom: SPACING.m,
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
  phone: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: SPACING.l,
  },
  progressDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginHorizontal: SPACING.s,
  },
  progressDotActive: {
    backgroundColor: COLORS.primary,
  },
  progressDotInactive: {
    backgroundColor: COLORS.border,
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
  genderContainer: {
    marginBottom: SPACING.m,
  },
  genderLabel: {
    fontSize: FONT_SIZES.m,
    fontWeight: '500',
    color: COLORS.text,
    marginBottom: SPACING.s,
  },
  genderButtons: {
    flexDirection: 'row',
    gap: SPACING.s,
  },
  genderButton: {
    flex: 1,
    paddingVertical: SPACING.m,
    paddingHorizontal: SPACING.m,
    borderRadius: BORDER_RADIUS.m,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  genderButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  genderButtonText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
  },
  genderButtonTextActive: {
    color: COLORS.white,
    fontWeight: '600',
  },
  button: {
    marginBottom: SPACING.m,
  },
  buttonContainer: {
    marginTop: SPACING.l,
  },
  footer: {
    marginTop: SPACING.l,
    marginBottom: SPACING.l,
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
