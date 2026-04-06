import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';

type CitySelectionScreenProps = {
  navigation: NativeStackNavigationProp<any, 'CitySelection'>;
  route: RouteProp<any, 'CitySelection'>;
};

export const CitySelectionScreen: React.FC<CitySelectionScreenProps> = ({ navigation, route }) => {
  const [cities, setCities] = useState<Array<{ id: number; name: string }>>([]);
  const [selectedCity, setSelectedCity] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const { error, ToastContainer } = useToast();

  useEffect(() => {
    loadCities();
  }, []);

  const loadCities = async () => {
    try {
      const response = await apiService.getCities();
      setCities(response.data);
    } catch (err: any) {
      error('Ошибка загрузки городов');
    }
  };

  const filteredCities = cities.filter((city) =>
    city.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const routeParams = route.params || { phone: '' };
  const { phone } = routeParams;

  const handleContinue = () => {
    if (!selectedCity) {
      error('Выберите город');
      return;
    }

    const city = cities.find((c) => c.id === selectedCity);
    navigation.navigate('Register', {
      phone,
      cityId: selectedCity,
      cityName: city?.name || '',
    });
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Выбор города</Text>
        <Text style={styles.subtitle}>Выберите ваш город</Text>
      </View>

      <View style={styles.content}>
        <Input
          placeholder="Поиск города..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />

        <ScrollView style={styles.citiesList} showsVerticalScrollIndicator={false}>
          {filteredCities.map((city) => (
            <TouchableOpacity
              key={city.id}
              style={[
                styles.cityItem,
                selectedCity === city.id && styles.cityItemSelected,
              ]}
              onPress={() => setSelectedCity(city.id)}
            >
              <Text
                style={[
                  styles.cityText,
                  selectedCity === city.id && styles.cityTextSelected,
                ]}
              >
                {city.name}
              </Text>
              {selectedCity === city.id && (
                <View style={styles.checkmark}>
                  <Text style={styles.checkmarkText}>✓</Text>
                </View>
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>

        <Button
          title="Продолжить"
          onPress={handleContinue}
          loading={loading}
          fullWidth
          size="large"
          disabled={!selectedCity}
        />
      </View>
      <ToastContainer />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    padding: SPACING.l,
    paddingTop: SPACING.xl,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
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
    flex: 1,
    padding: SPACING.l,
  },
  citiesList: {
    flex: 1,
    marginBottom: SPACING.l,
    maxHeight: 300,
  },
  cityItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.m,
    borderRadius: BORDER_RADIUS.m,
    backgroundColor: COLORS.white,
    marginBottom: SPACING.s,
    borderWidth: 1.5,
    borderColor: COLORS.border,
  },
  cityItemSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  cityText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
  },
  cityTextSelected: {
    fontWeight: '600',
    color: COLORS.primary,
  },
  checkmark: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmarkText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.white,
    fontWeight: '700',
  },
});
