import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Image,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Button } from '../components/Button';
import { LoadingScreen } from '../components/Loading';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Profile: undefined;
  Dashboard: undefined;
};

type SupportScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Profile'>;

interface SupportScreenProps {
  navigation: SupportScreenNavigationProp;
}

interface SelectedImage {
  uri: string;
  name: string;
  type: string;
}

const MAX_IMAGES = 3;

export const SupportScreen: React.FC<SupportScreenProps> = ({ navigation }) => {
  const [message, setMessage] = useState('');
  const [images, setImages] = useState<SelectedImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [helpText, setHelpText] = useState('');
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [canSend, setCanSend] = useState(true);
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    loadHelpInfo();
  }, []);

  const loadHelpInfo = async () => {
    try {
      const result = await apiService.getHelpInfo();
      const data = (result as any)?.data ?? result;
      if (data?.help_text) {
        setHelpText(data.help_text);
      }
      if (data?.can_use !== undefined) {
        setCanSend(data.can_use);
      }
      if (data?.cooldown_seconds) {
        setCooldownSeconds(data.cooldown_seconds);
      }
    } catch {
      // Silently fail - user can still try to send
    }
  };

  const pickImage = async () => {
    if (images.length >= MAX_IMAGES) {
      error(`Можно загрузить не более ${MAX_IMAGES} фото`);
      return;
    }

    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permissionResult.granted) {
      error('Необходимо предоставить доступ к галерее');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      const newImage: SelectedImage = {
        uri: asset.uri,
        name: `photo_${Date.now()}.jpg`,
        type: 'image/jpeg',
      };
      setImages([...images, newImage]);
    }
  };

  const removeImage = (index: number) => {
    setImages(images.filter((_, i) => i !== index));
  };

  const handleSend = async () => {
    if (!message.trim()) {
      error('Введите текст обращения');
      return;
    }

    if (!canSend && cooldownSeconds > 0) {
      const hours = Math.floor(cooldownSeconds / 3600);
      const minutes = Math.floor((cooldownSeconds % 3600) / 60);
      error(`Следующее обращение можно отправить через ${hours}ч ${minutes}мин`);
      return;
    }

    setLoading(true);
    try {
      await apiService.sendHelpMessage(message.trim(), images.length > 0 ? images : undefined);
      success('✓ Обращение отправлено руководству');
      setMessage('');
      setImages([]);
      setCanSend(false);
    } catch (err: any) {
      error(err.message || 'Ошибка отправки обращения');
    } finally {
      setLoading(false);
    }
  };

  const handleSOS = async () => {
    Alert.alert(
      '🆘 SOS-сигнал',
      'Отправить экстренный сигнал руководству? Это отправит ваш профиль и местоположение.',
      [
        { text: 'Отмена', style: 'cancel' },
        {
          text: 'Отправить SOS',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiService.sendHelpSignal();
              success('✓ SOS-сигнал отправлен руководству');
            } catch (err: any) {
              error(err.message || 'Ошибка отправки SOS');
            }
          },
        },
      ]
    );
  };

  const formatCooldown = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}ч ${minutes}мин`;
  };

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Поддержка" onBack={() => navigation.goBack()} />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Help Info */}
        {helpText ? (
          <View style={styles.infoCard}>
            <Text style={styles.infoText}>{helpText}</Text>
          </View>
        ) : null}

        {/* Cooldown Warning */}
        {!canSend && cooldownSeconds > 0 && (
          <View style={styles.cooldownCard}>
            <Ionicons name="time-outline" size={24} color={COLORS.warning} />
            <Text style={styles.cooldownText}>
              Следующее обращение можно отправить через {formatCooldown(cooldownSeconds)}
            </Text>
          </View>
        )}

        {/* Message Input */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Текст обращения</Text>
          <View style={styles.messageCard}>
            <TextInput
              style={styles.messageInput}
              value={message}
              onChangeText={setMessage}
              placeholder="Опишите вашу проблему или вопрос..."
              placeholderTextColor={COLORS.gray}
              multiline
              numberOfLines={6}
              textAlignVertical="top"
              maxLength={2000}
              editable={canSend || cooldownSeconds === 0}
            />
            <Text style={styles.charCount}>
              {message.length}/2000
            </Text>
          </View>
        </View>

        {/* Photo Upload */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Фотографии ({images.length}/{MAX_IMAGES})
          </Text>
          
          <View style={styles.imagesContainer}>
            {/* Image Preview Grid */}
            {images.map((img, index) => (
              <View key={index} style={styles.imageWrapper}>
                <Image source={{ uri: img.uri }} style={styles.imagePreview} />
                <TouchableOpacity
                  style={styles.imageRemove}
                  onPress={() => removeImage(index)}
                  activeOpacity={0.7}
                >
                  <Ionicons name="close-circle" size={24} color={COLORS.error} />
                </TouchableOpacity>
              </View>
            ))}

            {/* Add Image Button */}
            {images.length < MAX_IMAGES && (
              <TouchableOpacity
                style={styles.addImageButton}
                onPress={pickImage}
                activeOpacity={0.7}
              >
                <Ionicons name="camera-outline" size={32} color={COLORS.primary} />
                <Text style={styles.addImageText}>Добавить фото</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Send Button */}
        <Button
          title={loading ? 'Отправка...' : 'Отправить обращение'}
          onPress={handleSend}
          loading={loading}
          disabled={!canSend && cooldownSeconds > 0}
          fullWidth
          size="large"
        />

        {/* SOS Button */}
        <TouchableOpacity
          style={styles.sosButton}
          onPress={handleSOS}
          activeOpacity={0.8}
        >
          <Ionicons name="warning" size={20} color={COLORS.error} />
          <Text style={styles.sosButtonText}>SOS - Экстренный сигнал</Text>
        </TouchableOpacity>
      </ScrollView>

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
    padding: SPACING.l,
  },

  /* Info Card */
  infoCard: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.l,
    padding: SPACING.l,
    marginBottom: SPACING.l,
  },
  infoText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 22,
  },

  /* Cooldown Warning */
  cooldownCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.warning + '15',
    borderRadius: BORDER_RADIUS.l,
    padding: SPACING.m,
    marginBottom: SPACING.l,
    gap: SPACING.m,
  },
  cooldownText: {
    flex: 1,
    fontSize: FONT_SIZES.m,
    color: COLORS.warning,
    fontWeight: '600',
  },

  /* Section */
  section: {
    marginBottom: SPACING.l,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.s,
    fontWeight: '600',
    color: COLORS.gray,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: SPACING.s,
  },

  /* Message Input */
  messageCard: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.l,
    padding: SPACING.m,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  messageInput: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    minHeight: 120,
    maxHeight: 200,
  },
  charCount: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    textAlign: 'right',
    marginTop: SPACING.xs,
  },

  /* Images Container */
  imagesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.m,
  },
  imageWrapper: {
    width: 100,
    height: 100,
    borderRadius: BORDER_RADIUS.m,
    overflow: 'hidden',
    position: 'relative',
  },
  imagePreview: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  imageRemove: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: COLORS.white,
    borderRadius: 12,
  },
  addImageButton: {
    width: 100,
    height: 100,
    borderRadius: BORDER_RADIUS.m,
    backgroundColor: COLORS.white,
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.xs,
  },
  addImageText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.primary,
    fontWeight: '600',
  },

  /* SOS Button */
  sosButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.s,
    marginTop: SPACING.l,
    paddingVertical: SPACING.m,
    borderRadius: BORDER_RADIUS.l,
    borderWidth: 2,
    borderColor: COLORS.error,
    backgroundColor: COLORS.white,
  },
  sosButtonText: {
    fontSize: FONT_SIZES.m,
    fontWeight: '700',
    color: COLORS.error,
  },
});
