# AlgoritmPlus Mobile - App Flow

## Screen Flow Diagram

```
┌─────────────────┐
│  Entry Screen   │ ← Phone input
└────────┬────────┘
         │
    ┌────▼─────────────┐
    │ Check if exists  │
    └────┬──────────┬──┘
         │          │
    Exists    Doesn't Exist
         │          │
    ┌────▼────┐  ┌───▼──────────────┐
    │  Login  │  │ City Selection   │
    │Phone+INN│  └────────┬─────────┘
    └────┬────┘           │
         │           ┌────▼─────────────┐
         │           │    Register      │
         │           │ ФИО, ИНН, Card   │
         │           └────────┬─────────┘
         │                    │
         └────────┬───────────┘
                  │
         ┌────────▼─────────┐
         │    Dashboard     │ ← Main menu
         │  Stats + Grid    │
         └────────┬─────────┘
                  │
    ┌─────────────┼──────────────────┐
    │             │                   │
┌───▼──────┐ ┌───▼──────┐  ┌────────▼────────┐
│  Search  │ │   My     │  │     Wallet      │
│  Orders  │ │  Orders  │  │  Balance/Payout │
└──────────┘ └──────────┘  └─────────────────┘
                                   
┌───▼──────┐ ┌───────────┐  ┌─────────────────┐
│ Profile  │ │ Notifications │ │  Promotions    │
│  Settings│ │  Messages  │  │   & Bonuses     │
└──────────┘ └───────────┘  └─────────────────┘
```

## Main Screens Overview

### 1️⃣ Entry Screen
- Phone number input with formatting
- Continue button
- Link to login for existing users
- Privacy notice

### 2️⃣ Login Screen
- Phone + ИНН inputs
- Login button
- Redirect to registration link
- Error handling

### 3️⃣ City Selection
- Search input
- Scrollable city list
- Selection indicators
- Continue to registration

### 4️⃣ Registration
- Full name inputs (ФИО)
- Birthday picker (DD.MM.YYYY)
- ИНН input (12 digits)
- Bank card input
- Self-employment info modal
- Submit button

### 5️⃣ Dashboard
- User greeting (Last Name + First Name)
- 4 stat cards:
  - Balance
  - Rating coefficient
  - Total orders
  - Successful orders
- 6-item menu grid:
  - 🔍 Поиск заказов
  - 📋 Мои заказы
  - 💰 Кошелёк
  - 👤 Профиль
  - 📢 Уведомления
  - 🎁 Акции
- Pull-to-refresh

### 6️⃣ Search Orders
- Horizontal customer chips
- Order cards with:
  - Customer name & job type
  - Date and shift (day/night)
  - City and worker count
  - Adjusted payment
  - "Взять заказ" button
- Empty state
- Pull-to-refresh

### 7️⃣ My Orders
- Tab switcher:
  - Заявки (Applications)
  - Назначенные (Assigned)
- Order cards with actions:
  - Applications: "Отозвать заявку"
  - Assigned: "Отказаться" + "Подписать акт"
- Confirmation modals
- Pull-to-refresh

### 8️⃣ Wallet
- Large balance display
- Payout form:
  - Amount input
  - Minimum validation (2600₽)
  - Available balance hint
- Payment history list
- Wallet requests status
- Pull-to-refresh

### 9️⃣ Profile
- User card:
  - Avatar (initials)
  - Full name
  - City and phone
- Stats (rating, balance, orders)
- Personal info section:
  - ИНН
  - Birthday
  - Self-employment status
- Bank card management
- Action items:
  - 📜 Правила
  - 🎁 Реферальная программа
  - 💬 Поддержка
- Logout button

### 🔟 Notifications
- Unread count header
- "Прочитать все" button
- Notification cards:
  - Type-based icon
  - Title and message
  - Relative timestamp
  - Unread indicator
- Pull-to-refresh

### 1️⃣1️⃣ Promotions
- Active promotion cards:
  - Type icon and badge
  - Title and bonus amount
  - Description
  - Progress bar (if joined)
  - "Участвовать" button
  - Date range
- Bonus history list
- Pull-to-refresh

## Component Library

### Button
- **Variants**: Primary, Secondary, Outline, Danger
- **Sizes**: Small, Medium, Large
- **States**: Normal, Disabled, Loading
- **Features**: Full-width, icon support

### Input
- **Features**: Label, placeholder, validation
- **Types**: Text, phone, numeric, password
- **States**: Focused, Error, Disabled
- **Extras**: Hints, icons, right elements

### Card
- **Variants**: Shadow (default), Outlined, Filled
- **Padding**: None, Small, Medium, Large
- **Content**: Optional title/subtitle header

### Modal
- **Types**: Custom, Confirmation, Info
- **Features**: 
  - Scrollable content
  - Custom footer
  - Close button toggle
  - Overlay background

### Toast
- **Types**: Success ✓, Error ✕, Info ℹ, Warning ⚠
- **Animation**: Slide down + fade
- **Auto-hide**: 3 seconds
- **Position**: Top of screen

### Loading
- **Types**: Inline, Full-screen
- **Features**: Optional text
- **Overlay**: Semi-transparent background

## Navigation Structure

```
Stack Navigator
├── Entry
├── Login
├── Register
├── CitySelection
├── Dashboard
├── SearchOrders
├── MyOrders
├── Wallet
├── Profile
├── Notifications
└── Promotions
```

**Animation**: Slide from right  
**Header**: Hidden (custom headers in screens)  
**Status Bar**: Dark icons  

## Data Flow

```
User Action
    ↓
Component Event Handler
    ↓
API Service (axios)
    ↓
Backend (/api/v1/*)
    ↓
Response Processing
    ↓
State Update (useState)
    ↓
UI Re-render
    ↓
Toast Notification
```

## Storage Keys

```
@algoritmplus_token     - JWT auth token
@algoritmplus_user      - User data (JSON)
@algoritmplus_city      - Selected city
@algoritmplus_role      - User role
```

## API Endpoints Used

### Auth
- POST `/auth/telegram-webapp`
- POST `/auth/check-user`
- POST `/auth/login-phone`
- POST `/auth/logout`

### Profile
- GET `/profile/me`
- GET `/profile/me/rating`
- GET `/profile/me/about-panel`
- POST `/profile/me/bank-card`
- POST `/profile/me/change-city-request`
- POST `/profile/me/security-data`
- GET `/profile/me/referral-pack`
- POST `/profile/me/create-payment`
- GET `/profile/me/pending-contracts`
- POST `/profile/me/ensure-contracts`

### Orders
- GET `/search/order-customers`
- GET `/search/orders`
- GET `/search/orders/{id}/apply-preview`
- POST `/search/orders/{id}/applications`

### Applications
- GET `/applications/orders`
- DELETE `/applications/orders/{id}/application`
- DELETE `/applications/orders/{id}/assignment`
- GET `/applications/orders/{id}/refusal-notice`

### Notifications
- GET `/notifications/`
- POST `/notifications/mark-read`

### Promotions
- GET `/promotions/`
- POST `/promotions/{id}/join`
- POST `/promotions/cancel-all`
- GET `/promotions/bonuses`

### Meta
- GET `/meta/panel-menu`
- GET `/meta/cities`
- GET `/meta/worker-rules`
- GET `/meta/bot-logo`

---

**Total**: 10 screens, 6 components, 30+ API endpoints, fully typed
