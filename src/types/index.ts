// User types
export interface User {
  id: number;
  tgId: number;
  phone: string;
  firstName: string;
  lastName: string;
  middleName?: string;
  inn: string;
  city: string;
  birthday: string;
  bankCard?: string;
  passportData?: PassportData;
  isSelfEmployed: boolean;
  balance: number;
  rating: number;
  role: UserRole;
}

export interface PassportData {
  series: string;
  number: string;
  issuedBy: string;
  issueDate: string;
  registrationAddress: string;
}

export type UserRole = 'worker' | 'admin' | 'manager' | 'customer' | 'accountant' | 'director' | 'foreman';

// Order types
export interface Order {
  id: number;
  customerId: number;
  customerName: string;
  organization: string;
  jobId: number;
  jobName: string;
  date: string;
  shift: 'day' | 'night';
  workersRequired: number;
  workersCount: number;
  city: string;
  amount: number;
  adjustedAmount?: number;
  ratingCoefficient: number;
  status: OrderStatus;
}

export type OrderStatus = 'active' | 'completed' | 'cancelled';

export interface OrderApplication {
  id: number;
  orderId: number;
  userId: number;
  status: ApplicationStatus;
  createdAt: string;
  order: Order;
}

export type ApplicationStatus = 'pending' | 'confirmed' | 'withdrawn' | 'rejected';

export interface AssignedOrder {
  id: number;
  orderId: number;
  userId: number;
  status: AssignedStatus;
  order: Order;
  payment?: number;
  isActSigned: boolean;
}

export type AssignedStatus = 'assigned' | 'completed' | 'refused';

// City types
export interface City {
  id: number;
  name: string;
}

// Customer types
export interface Customer {
  id: number;
  name: string;
  organization: string;
  logo?: string;
}

// Notification types
export interface Notification {
  id: number;
  userId: number;
  title: string;
  message: string;
  type: NotificationType;
  isRead: boolean;
  createdAt: string;
}

export type NotificationType = 'order' | 'payment' | 'system' | 'promotion';

// Promotion types
export interface Promotion {
  id: number;
  title: string;
  description: string;
  type: PromotionType;
  startDate: string;
  endDate: string;
  bonus: number;
  conditions: PromotionConditions;
  userProgress?: UserPromotionProgress;
}

export type PromotionType = 'streak' | 'period' | 'city' | 'referral';

export interface PromotionConditions {
  minOrders?: number;
  consecutiveDays?: number;
  cityId?: number;
  periodDays?: number;
}

export interface UserPromotionProgress {
  promotionId: number;
  currentProgress: number;
  targetProgress: number;
  isCompleted: boolean;
  bonusReceived: boolean;
}

// Payment types
export interface WalletPayment {
  id: number;
  userId: number;
  amount: number;
  status: PaymentStatus;
  createdAt: string;
  processedAt?: string;
  actSigned: boolean;
}

export type PaymentStatus = 'pending' | 'processing' | 'completed' | 'rejected';

export interface PaymentHistory {
  id: number;
  orderId: number;
  amount: number;
  date: string;
  type: 'order' | 'bonus' | 'referral';
}

// Rating types
export interface UserRating {
  userId: number;
  totalOrders: number;
  successfulOrders: number;
  plus: number;
  minus: number;
  coefficient: number;
}

// Auth types
export interface LoginCredentials {
  phone: string;
  inn: string;
}

export interface RegisterData {
  phone: string;
  firstName: string;
  lastName: string;
  middleName?: string;
  birthday: string;
  inn: string;
  city: string;
  bankCard: string;
}

export interface VerificationCode {
  phone: string;
  code: string;
}

// Contract types
export interface Contract {
  id: number;
  userId: number;
  legalEntity: string;
  signedAt?: string;
  status: 'pending' | 'signed';
}

// Support types
export interface SupportRequest {
  id: number;
  userId: number;
  message: string;
  attachments?: string[];
  status: 'open' | 'closed';
  createdAt: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  message: string;
  code: string;
  details?: any;
}

// Menu types
export interface MenuItem {
  id: string;
  title: string;
  icon: string;
  screen: string;
  color: string;
}

export interface PanelMenu {
  items: MenuItem[];
}
