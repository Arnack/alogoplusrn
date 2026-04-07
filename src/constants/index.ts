import { MenuItem } from '../types';

// API Configuration
export const API_BASE_URL = 'https://algoritmplus.online/api/v1';
export const API_TIMEOUT = 30000;

// App Colors - Clean, strict theme
export const COLORS = {
  // Primary
  primary: '#1a1a2e',
  primaryLight: '#16213e',
  primaryDark: '#0f0f1a',
  
  // Accent
  accent: '#0f3460',
  accentLight: '#1a4a7a',
  
  // Status colors
  success: '#27ae60',
  successLight: '#2ecc71',
  warning: '#f39c12',
  warningLight: '#f1c40f',
  error: '#e74c3c',
  errorLight: '#ff6b6b',
  info: '#3498db',
  infoLight: '#5dade2',
  
  // Neutral
  white: '#ffffff',
  black: '#000000',
  gray: '#95a5a6',
  grayLight: '#ecf0f1',
  grayDark: '#7f8c8d',
  
  // Background
  background: '#f5f6fa',
  backgroundDark: '#dfe4ea',
  card: '#ffffff',
  
  // Text
  text: '#2c3e50',
  textLight: '#7f8c8d',
  textDark: '#2c3e50',
  
  // Border
  border: '#dfe6e9',
  borderDark: '#b2bec3',
  
  // Shift colors
  day: '#3498db',
  night: '#9b59b6',
};

// Spacing
export const SPACING = {
  xs: 4,
  s: 8,
  m: 16,
  l: 24,
  xl: 32,
  xxl: 48,
};

// Border Radius
export const BORDER_RADIUS = {
  s: 4,
  m: 8,
  l: 12,
  xl: 16,
  round: 999,
};

// Typography
export const FONTS = {
  regular: 'System',
  medium: 'System',
  bold: 'System',
};

export const FONT_SIZES = {
  xs: 12,
  s: 14,
  m: 16,
  l: 18,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

// Main Dashboard Menu Items
export const MAIN_MENU_ITEMS: MenuItem[] = [
  {
    id: 'search_orders',
    title: 'Поиск заявок',
    icon: '🔍',
    screen: 'SearchOrders',
    color: COLORS.primary,
  },
  {
    id: 'my_orders',
    title: 'Мои заказы',
    icon: '📋',
    screen: 'MyOrders',
    color: COLORS.info,
  },
  {
    id: 'wallet',
    title: 'Кошелёк',
    icon: '💰',
    screen: 'Wallet',
    color: COLORS.success,
  },
  {
    id: 'profile',
    title: 'Профиль',
    icon: '👤',
    screen: 'Profile',
    color: COLORS.accent,
  },
  {
    id: 'notifications',
    title: 'Уведомления',
    icon: '📢',
    screen: 'Notifications',
    color: COLORS.warning,
  },
  {
    id: 'promotions',
    title: 'Акции',
    icon: '🎁',
    screen: 'Promotions',
    color: COLORS.error,
  },
];

// Minimum payout amount
export const MINIMUM_PAYOUT = 2600;

// Shift times
export const SHIFT_TIMES = {
  day: '08:00 - 20:00',
  night: '20:00 - 08:00',
};

// Storage keys
export const STORAGE_KEYS = {
  TOKEN: '@algoritmplus_token',
  USER: '@algoritmplus_user',
  CITY: '@algoritmplus_city',
  ROLE: '@algoritmplus_role',
};

// Validation patterns
export const PATTERNS = {
  PHONE: /^\+7\d{10}$/,
  INN: /^\d{12}$/,
  CARD: /^\d{16,19}$/,
  DATE: /^\d{2}\.\d{2}\.\d{4}$/,
};

// Error messages
export const ERROR_MESSAGES = {
  NETWORK: 'Ошибка сети. Проверьте подключение к интернету.',
  UNAUTHORIZED: 'Пользователь не авторизован.',
  SERVER: 'Ошибка сервера. Попробуйте позже.',
  VALIDATION: 'Проверьте правильность ввода данных.',
};

// Success messages
export const SUCCESS_MESSAGES = {
  LOGIN: 'Вы успешно вошли.',
  REGISTER: 'Регистрация завершена.',
  LOGOUT: 'Вы вышли из аккаунта.',
  APPLICATION_CREATED: 'Заявка создана.',
  APPLICATION_WITHDRAWN: 'Заявка отозвана.',
  PAYMENT_CREATED: 'Заявка на выплату создана.',
  DATA_UPDATED: 'Данные обновлены.',
};
