import React, { useEffect, useRef } from 'react';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { setupNotificationHandlers } from '../services/pushNotifications';

// Screens
import { EntryScreen } from '../screens/EntryScreen';
import { LoginScreen } from '../screens/LoginScreen';
import { RegisterScreen } from '../screens/RegisterScreen';
import { RegisterLastNameScreen } from '../screens/RegisterLastNameScreen';
import { RegisterInnScreen } from '../screens/RegisterInnScreen';
import { RegisterCardScreen } from '../screens/RegisterCardScreen';
import { RegisterPhoneScreen } from '../screens/RegisterPhoneScreen';
import { RegisterPhoneConfirmScreen } from '../screens/RegisterPhoneConfirmScreen';
import { RegisterAgreementScreen } from '../screens/RegisterAgreementScreen';
import { RegisterAgreementConfirmScreen } from '../screens/RegisterAgreementConfirmScreen';
import { RegisterSuccessScreen } from '../screens/RegisterSuccessScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { SearchOrdersScreen } from '../screens/SearchOrdersScreen';
import { MyOrdersScreen } from '../screens/MyOrdersScreen';
import { WalletScreen } from '../screens/WalletScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { RemoveAccountScreen } from '../screens/RemoveAccountScreen';
import { NotificationsScreen } from '../screens/NotificationsScreen';
import { PromotionsScreen } from '../screens/PromotionsScreen';
import { SupportScreen } from '../screens/SupportScreen';

// Theme
import { COLORS } from '../constants';

export type RootStackParamList = {
  Entry: undefined;
  Login: undefined;
  Register: { phone: string };
  RegisterCity: { phone: string };
  RegisterLastName: { phone: string; city: string };
  RegisterInn: { phone: string; city: string; lastName: string; firstName: string; middleName: string };
  RegisterCard: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string };
  RegisterPhone: { city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterPhoneConfirm: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterAgreement: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterAgreementConfirm: { phone: string; city: string; lastName: string; firstName: string; middleName: string; inn: string; card: string };
  RegisterSuccess: undefined;
  Dashboard: undefined;
  SearchOrders: undefined;
  MyOrders: undefined;
  Wallet: undefined;
  Profile: undefined;
  RemoveAccount: undefined;
  Notifications: undefined;
  Promotions: undefined;
  Support: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export const AppNavigator: React.FC = () => {
  const navRef = useRef<NavigationContainerRef<RootStackParamList>>(null);

  useEffect(() => {
    const cleanup = setupNotificationHandlers(
      () => {}, // foreground: nothing extra needed, polling handles refresh
      () => navRef.current?.navigate('Notifications'),
    );
    return cleanup;
  }, []);

  return (
    <NavigationContainer ref={navRef}>
      <Stack.Navigator
        initialRouteName="Entry"
        screenOptions={{
          headerShown: false,
          contentStyle: {
            backgroundColor: COLORS.background,
          },
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen name="Entry" component={EntryScreen} />
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="RegisterLastName" component={RegisterLastNameScreen} />
        <Stack.Screen name="RegisterInn" component={RegisterInnScreen} />
        <Stack.Screen name="RegisterCard" component={RegisterCardScreen} />
        <Stack.Screen name="RegisterPhone" component={RegisterPhoneScreen} />
        <Stack.Screen name="RegisterPhoneConfirm" component={RegisterPhoneConfirmScreen} />
        <Stack.Screen name="RegisterAgreement" component={RegisterAgreementScreen} />
        <Stack.Screen name="RegisterAgreementConfirm" component={RegisterAgreementConfirmScreen} />
        <Stack.Screen name="RegisterSuccess" component={RegisterSuccessScreen} />
        <Stack.Screen name="Dashboard" component={DashboardScreen} />
        <Stack.Screen name="SearchOrders" component={SearchOrdersScreen} />
        <Stack.Screen name="MyOrders" component={MyOrdersScreen} />
        <Stack.Screen name="Wallet" component={WalletScreen} />
        <Stack.Screen name="Profile" component={ProfileScreen} />
        <Stack.Screen name="RemoveAccount" component={RemoveAccountScreen} />
        <Stack.Screen name="Notifications" component={NotificationsScreen} />
        <Stack.Screen name="Promotions" component={PromotionsScreen} />
        <Stack.Screen name="Support" component={SupportScreen} />
      </Stack.Navigator>
      <StatusBar style="dark" />
    </NavigationContainer>
  );
};
