import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL, API_TIMEOUT, ERROR_MESSAGES } from '../constants';
import { storage } from '../utils/storage';
import type { ApiResponse, ApiError } from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add auth token
    this.api.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        const token = await storage.getToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - clear storage and redirect to login
          storage.clearAll();
        }
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: AxiosError<ApiError>): Error {
    if (error.response) {
      const { message, code } = error.response.data;
      return new Error(message || ERROR_MESSAGES.SERVER);
    } else if (error.request) {
      return new Error(ERROR_MESSAGES.NETWORK);
    }
    return new Error(error.message || ERROR_MESSAGES.SERVER);
  }

  // Auth endpoints
  async telegramWebAppAuth(initData: string) {
    const response = await this.api.post<ApiResponse<{ token: string; user: any }>>('/auth/telegram-webapp', {
      initData,
    });
    return response.data;
  }

  async checkUser(phone: string, city: string) {
    const response = await this.api.post<ApiResponse<{ exists: boolean; needsRegistration: boolean }>>('/auth/check-user', {
      phone,
      city,
    });
    return response.data;
  }

  async loginPhone(phone: string, innLast4: string, city: string) {
    const response = await this.api.post<{ access_token: string; token_type: string; expires_in: number }>('/auth/login-phone', {
      phone,
      inn_last4: innLast4,
      city,
    });
    return response.data;
  }

  async logout() {
    const response = await this.api.post<ApiResponse<void>>('/auth/logout');
    return response.data;
  }

  // Profile endpoints
  async getMe() {
    const response = await this.api.get<ApiResponse<any>>('/users/me');
    return response.data;
  }

  async getProfileAboutPanel() {
    const response = await this.api.get<ApiResponse<any>>('/users/me/about-panel');
    return response.data;
  }

  async getRating() {
    const response = await this.api.get<ApiResponse<any>>('/users/me/rating');
    return response.data;
  }

  async updateBankCard(card: string, innLast4: string) {
    const response = await this.api.post('/users/me/bank-card', { card, inn_last4: innLast4 });
    return response.data;
  }

  async requestCityChange(cityId: number) {
    const response = await this.api.post<ApiResponse<void>>('/users/me/change-city-request', { cityId });
    return response.data;
  }

  async updateSecurityData(data: any) {
    const response = await this.api.post<ApiResponse<void>>('/users/me/security-data', data);
    return response.data;
  }

  async getReferralInfo() {
    const response = await this.api.get<ApiResponse<any>>('/users/me/referral-pack');
    return response.data;
  }

  async createPayment(amount: number) {
    const response = await this.api.post<ApiResponse<any>>('/users/me/create-payment', { amount });
    return response.data;
  }

  async getPendingContracts() {
    const response = await this.api.get<ApiResponse<any[]>>('/users/me/pending-contracts');
    return response.data;
  }

  async ensureContracts(pin: string) {
    const response = await this.api.post<ApiResponse<void>>('/users/me/ensure-contracts', { pin });
    return response.data;
  }

  // Search endpoints
  async getOrderCustomers() {
    const response = await this.api.get<any>('/search/order-customers');
    return response.data;
  }

  async searchOrders(customerId: number) {
    const response = await this.api.get<any>('/search/orders', {
      params: { customer_id: customerId },
    });
    return response.data;
  }

  async getOrderApplyPreview(orderId: number) {
    const response = await this.api.get<any>(`/search/orders/${orderId}/apply-preview`);
    return response.data;
  }

  async createOrderApplication(orderId: number) {
    const response = await this.api.post<any>(`/search/orders/${orderId}/applications`, { order_from_friend: false });
    return response.data;
  }

  // Applications endpoints
  async getMyOrders(params?: { status?: string }) {
    const response = await this.api.get<ApiResponse<any>>('/applications/orders', { params });
    return response.data;
  }

  async withdrawApplication(orderId: number) {
    const response = await this.api.delete<ApiResponse<void>>(`/applications/orders/${orderId}/application`);
    return response.data;
  }

  async refuseAssignment(orderId: number) {
    const response = await this.api.delete<ApiResponse<void>>(`/applications/orders/${orderId}/assignment`);
    return response.data;
  }

  async getRefusalNotice(orderId: number) {
    const response = await this.api.get<ApiResponse<{ notice: string }>>(`/applications/orders/${orderId}/refusal-notice`);
    return response.data;
  }

  // Notifications endpoints
  async getNotifications() {
    const response = await this.api.get<ApiResponse<any[]>>('/notifications/');
    return response.data;
  }

  async markNotificationsAsRead(ids: number[]) {
    const response = await this.api.post<ApiResponse<void>>('/notifications/mark-read', { ids });
    return response.data;
  }

  // Promotions endpoints
  async getPromotions() {
    const response = await this.api.get<ApiResponse<any[]>>('/promotions/');
    return response.data;
  }

  async joinPromotion(promotionId: number) {
    const response = await this.api.post<ApiResponse<void>>(`/promotions/${promotionId}/join`);
    return response.data;
  }

  async getBonuses() {
    const response = await this.api.get<ApiResponse<any[]>>('/promotions/bonuses');
    return response.data;
  }

  // Meta endpoints
  async getCities() {
    const response = await this.api.get<ApiResponse<any[]>>('/meta/cities');
    return response.data;
  }

  async getWorkerRules() {
    const response = await this.api.get<ApiResponse<{ text: string }>>('/meta/worker-rules');
    return response.data;
  }

  async getPanelMenu() {
    const response = await this.api.get<ApiResponse<any>>('/meta/panel-menu');
    return response.data;
  }
}

export const apiService = new ApiService();
