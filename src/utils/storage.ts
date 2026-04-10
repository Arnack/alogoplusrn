import AsyncStorage from '@react-native-async-storage/async-storage';
import { STORAGE_KEYS } from '../constants';

export const storage = {
  async getToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(STORAGE_KEYS.TOKEN);
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  },

  async setToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.TOKEN, token);
    } catch (error) {
      console.error('Error setting token:', error);
    }
  },

  async removeToken(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.TOKEN);
    } catch (error) {
      console.error('Error removing token:', error);
    }
  },

  async getUser(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(STORAGE_KEYS.USER);
    } catch (error) {
      console.error('Error getting user:', error);
      return null;
    }
  },

  async setUser(user: string): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.USER, user);
    } catch (error) {
      console.error('Error setting user:', error);
    }
  },

  async removeUser(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.USER);
    } catch (error) {
      console.error('Error removing user:', error);
    }
  },

  async getCity(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(STORAGE_KEYS.CITY);
    } catch (error) {
      console.error('Error getting city:', error);
      return null;
    }
  },

  async setCity(city: string): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.CITY, city);
    } catch (error) {
      console.error('Error setting city:', error);
    }
  },

  async removeCity(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.CITY);
    } catch (error) {
      console.error('Error removing city:', error);
    }
  },

  async clearAll(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        STORAGE_KEYS.TOKEN,
        STORAGE_KEYS.USER,
        STORAGE_KEYS.CITY,
        STORAGE_KEYS.ROLE,
      ]);
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  },

  async get(key: string): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(key);
    } catch (error) {
      console.error(`Error getting ${key}:`, error);
      return null;
    }
  },

  async set(key: string, value: string): Promise<void> {
    try {
      await AsyncStorage.setItem(key, value);
    } catch (error) {
      console.error(`Error setting ${key}:`, error);
    }
  },

  async remove(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing ${key}:`, error);
    }
  },
};
