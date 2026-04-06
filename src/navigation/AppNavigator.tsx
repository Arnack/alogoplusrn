import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';

// Screens
import { EntryScreen } from '../screens/EntryScreen';
import { LoginScreen } from '../screens/LoginScreen';
import { RegisterScreen } from '../screens/RegisterScreen';
import { CitySelectionScreen } from '../screens/CitySelectionScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { SearchOrdersScreen } from '../screens/SearchOrdersScreen';
import { MyOrdersScreen } from '../screens/MyOrdersScreen';
import { WalletScreen } from '../screens/WalletScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { NotificationsScreen } from '../screens/NotificationsScreen';
import { PromotionsScreen } from '../screens/PromotionsScreen';

// Theme
import { COLORS } from '../constants';

export type RootStackParamList = {
  Entry: undefined;
  Login: undefined;
  Register: { phone: string; cityId: number; cityName: string };
  CitySelection: { phone: string };
  Dashboard: undefined;
  SearchOrders: undefined;
  MyOrders: undefined;
  Wallet: undefined;
  Profile: undefined;
  Notifications: undefined;
  Promotions: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export const AppNavigator: React.FC = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Entry"
        screenOptions={{
          headerShown: false,
          contentStyle: {
            backgroundColor: COLORS.background,
          },
          animation: 'slide_from_right',
          statusBarStyle: 'dark',
        }}
      >
        <Stack.Screen name="Entry" component={EntryScreen} />
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="CitySelection" component={CitySelectionScreen} />
        <Stack.Screen name="Dashboard" component={DashboardScreen} />
        <Stack.Screen name="SearchOrders" component={SearchOrdersScreen} />
        <Stack.Screen name="MyOrders" component={MyOrdersScreen} />
        <Stack.Screen name="Wallet" component={WalletScreen} />
        <Stack.Screen name="Profile" component={ProfileScreen} />
        <Stack.Screen name="Notifications" component={NotificationsScreen} />
        <Stack.Screen name="Promotions" component={PromotionsScreen} />
      </Stack.Navigator>
      <StatusBar style="dark" />
    </NavigationContainer>
  );
};
