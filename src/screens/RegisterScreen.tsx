import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
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

type RegisterScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Register'>;

type RegisterScreenProps = {
  navigation: RegisterScreenNavigationProp;
  route: RouteProp<RootStackParamList, 'Register'>;
};

export const RegisterScreen: React.FC<RegisterScreenProps> = ({ navigation, route }) => {
  const { phone = '' } = route.params || {};
  const [city, setCity] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [cities, setCities] = useState<string[]>([]);
  const { error, ToastContainer } = useToast();

  useEffect(() => {
    apiService.getCities().then((result: any) => {
      const data = result?.data ?? result;
      if (Array.isArray(data)) setCities(data.map((c: any) => c.name));
    }).catch(() => {});
  }, []);

  const filteredCities = cities.filter(c =>
    c.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleContinue = () => {
    if (!city) {
      error('Выберите город');
      return;
    }
    navigation.navigate('RegisterLastName', { phone, city });
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Регистрация" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>Выберите ваш город</Text>

          <View style={styles.content}>
            <Input
              label="Поиск города"
              value={searchQuery}
              onChangeText={setSearchQuery}
              placeholder="Начните вводить город"
            />

            <ScrollView style={styles.cityList} nestedScrollEnabled showsVerticalScrollIndicator={false}>
              {filteredCities.length === 0 && (
                <Text style={styles.noCities}>Город не найден</Text>
              )}
              {filteredCities.map((c) => (
                <View
                  key={c}
                  style={[
                    styles.cityItem,
                    city === c && styles.cityItemSelected,
                  ]}
                >
                  <Button
                    title={c}
                    onPress={() => setCity(c)}
                    variant={city === c ? 'primary' : 'outline'}
                    fullWidth
                    size="medium"
                  />
                </View>
              ))}
            </ScrollView>

            <Button
              title="Продолжить"
              onPress={handleContinue}
              loading={loading}
              fullWidth
              size="large"
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
  cityList: {
    maxHeight: 300,
    marginBottom: SPACING.m,
  },
  cityItem: {
    marginBottom: SPACING.xs,
  },
  cityItemSelected: {
    // handled by button variant
  },
  button: {
    marginTop: SPACING.s,
  },
  noCities: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
    textAlign: 'center',
    paddingVertical: SPACING.l,
  },
});
