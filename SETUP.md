# AlgoritmPlus Mobile - Setup Guide

## Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Expo CLI
- iOS Simulator (for Mac) or Android Emulator
- Expo Go app (for testing on physical device)

## Quick Start

### 1. Install Dependencies

```bash
npm install --legacy-peer-deps
```

### 2. Configure API URL

Edit `src/constants/index.ts` and update the API_BASE_URL:

```typescript
export const API_BASE_URL = 'https://your-api-domain.com/api/v1';
```

### 3. Start the App

```bash
# Start Expo dev server
npm start

# Or run directly on a platform
npm run ios     # iOS Simulator
npm run android # Android Emulator
```

### 4. Test on Physical Device

1. Install Expo Go on your phone:
   - iOS: App Store
   - Android: Google Play Store
2. Scan the QR code from the terminal
3. The app will load on your device

## Project Structure

```
AlgoritmPlusMobile/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Button.tsx      # Button component
│   │   ├── Input.tsx       # Input field
│   │   ├── Card.tsx        # Card components
│   │   ├── Modal.tsx       # Modal dialogs
│   │   ├── Toast.tsx       # Toast notifications
│   │   └── Loading.tsx     # Loading indicators
│   │
│   ├── screens/            # App screens
│   │   ├── EntryScreen.tsx         # Initial entry point
│   │   ├── LoginScreen.tsx         # Login with phone + INN
│   │   ├── RegisterScreen.tsx      # Registration form
│   │   ├── CitySelectionScreen.tsx # City picker
│   │   ├── DashboardScreen.tsx     # Main dashboard
│   │   ├── SearchOrdersScreen.tsx  # Browse orders
│   │   ├── MyOrdersScreen.tsx      # User's orders
│   │   ├── WalletScreen.tsx        # Wallet & payouts
│   │   ├── ProfileScreen.tsx       # User profile
│   │   ├── NotificationsScreen.tsx # Notifications
│   │   └── PromotionsScreen.tsx    # Promotions
│   │
│   ├── services/           # API and external services
│   │   └── api.ts          # REST API client
│   │
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts        # All types
│   │
│   ├── constants/          # App constants and theme
│   │   └── index.ts        # Colors, spacing, fonts, menu
│   │
│   ├── utils/              # Utility functions
│   │   └── storage.ts      # AsyncStorage wrapper
│   │
│   └── navigation/         # Navigation configuration
│       └── AppNavigator.tsx
│
├── assets/                 # Images, fonts, etc.
├── App.tsx                 # Root component
├── index.js                # Entry point
├── app.json                # Expo configuration
├── babel.config.js         # Babel configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Dependencies
```

## Features Implemented

### Authentication Flow
✓ Phone number input with formatting
✓ User existence check
✓ Login with phone + INN
✓ Registration with city selection
✓ Profile data collection (name, INN, birthday, card)
✓ Self-employment status verification

### Main Dashboard
✓ User greeting with name
✓ Stats overview (balance, rating, orders)
✓ Menu grid with 6 main sections
✓ Pull-to-refresh functionality

### Order Search
✓ Customer list with horizontal scroll
✓ Order listing with details
✓ Shift badges (day/night)
✓ Apply to orders
✓ Order preview before applying

### My Orders
✓ Tab navigation (Applications / Assigned)
✓ Withdraw application
✓ Refuse assigned order
✓ Sign act functionality
✓ Confirmation modals

### Wallet
✓ Balance display
✓ Payout form with validation
✓ Minimum payout check (2600₽)
✓ Payment history
✓ Wallet payment status

### Profile
✓ User information display
✓ Rating statistics
✓ Bank card management
✓ Rules viewer
✓ Referral program info
✓ Support contact
✓ Logout confirmation

### Notifications
✓ Notification list
✓ Unread indicators
✓ Mark all as read
✓ Type-based icons
✓ Relative time formatting

### Promotions
✓ Active promotions display
✓ Join functionality
✓ Progress tracking
✓ Bonus history
✓ Type badges

## UI/UX Design

### Color Scheme
- Primary: #1a1a2e (Dark navy)
- Accent: #0f3460 (Blue)
- Success: #27ae60 (Green)
- Warning: #f39c12 (Orange)
- Error: #e74c3c (Red)
- Info: #3498db (Blue)

### Typography
- Clean system fonts
- Hierarchical sizing (xs to xxxl)
- Consistent weights (regular, medium, bold)

### Spacing
- Consistent spacing scale (4, 8, 16, 24, 32, 48)
- Card-based layouts with shadows
- Border radius for modern look

### Components
- Reusable button with variants
- Form inputs with validation
- Modal dialogs
- Toast notifications
- Loading states
- Stat cards

## API Integration

The app is designed to work with the existing FastAPI backend:

### Auth Endpoints
- POST `/auth/telegram-webapp` - Telegram WebApp auth
- POST `/auth/check-user` - Check if user exists
- POST `/auth/login-phone` - Phone + INN login
- POST `/auth/logout` - Logout

### Profile Endpoints
- GET `/profile/me` - Get current user
- GET `/profile/me/rating` - Get user rating
- POST `/profile/me/bank-card` - Update bank card
- GET `/profile/me/referral-pack` - Referral info

### Order Endpoints
- GET `/search/order-customers` - List customers
- GET `/search/orders` - Search orders
- GET `/search/orders/{id}/apply-preview` - Preview application
- POST `/search/orders/{id}/applications` - Apply to order

### Applications Endpoints
- GET `/applications/orders` - My orders
- DELETE `/applications/orders/{id}/application` - Withdraw
- DELETE `/applications/orders/{id}/assignment` - Refuse

### Other Endpoints
- Notifications (GET, POST)
- Promotions (GET, POST)
- Meta endpoints (cities, rules, menu)

## Building for Production

### iOS

```bash
# Build for iOS
eas build --platform ios

# Submit to App Store
eas submit --platform ios
```

### Android

```bash
# Build for Android
eas build --platform android

# Submit to Google Play
eas submit --platform android
```

## Environment Variables

Create a `.env` file in the root:

```env
API_BASE_URL=https://your-api-url.com/api/v1
```

## Troubleshooting

### Dependency Issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install --legacy-peer-deps
```

### Expo Cache
```bash
# Clear Expo cache
expo start -c
```

### TypeScript Errors
```bash
# Check TypeScript
npx tsc --noEmit
```

## Next Steps

1. Add push notification support
2. Implement offline mode with better caching
3. Add biometric authentication
4. Implement contract signing flow
5. Add SMS verification
6. Add photo upload for support
7. Implement order for friend feature
8. Add rating details screen

## Support

For issues or questions, contact the development team.
