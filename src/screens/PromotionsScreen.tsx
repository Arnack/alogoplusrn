import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants';
import { Card, StatCard } from '../components/Card';
import { Button } from '../components/Button';
import { LoadingScreen } from '../components/Loading';
import { SafeView } from '../components/SafeView';
import { ScreenHeader } from '../components/ScreenHeader';
import { useToast } from '../components/Toast';
import { apiService } from '../services/api';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Dashboard: undefined;
  Promotions: undefined;
};

type PromotionsScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Promotions'>;

interface PromotionsScreenProps {
  navigation: PromotionsScreenNavigationProp;
}

export const PromotionsScreen: React.FC<PromotionsScreenProps> = ({ navigation }) => {
  const [promotions, setPromotions] = useState<any[]>([]);
  const [bonuses, setBonuses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [joiningId, setJoiningId] = useState<number | null>(null);
  const { success, error, ToastContainer } = useToast();

  useEffect(() => {
    loadPromotions();
  }, []);

  const loadPromotions = async () => {
    setLoading(true);
    try {
      const data = await apiService.getPromotions();
      setPromotions(Array.isArray(data) ? data : (data as any)?.data || []);
      // In real app, load bonuses too
      setBonuses([]);
    } catch (err: any) {
      error('Ошибка загрузки акций');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPromotions();
    setRefreshing(false);
  };

  const handleJoin = async (promotionId: number) => {
    setJoiningId(promotionId);
    try {
      await apiService.joinPromotion(promotionId);
      success('Вы присоединились к акции');
      await loadPromotions();
    } catch (err: any) {
      error(err.message);
    } finally {
      setJoiningId(null);
    }
  };

  const getPromotionIcon = (type: string) => {
    switch (type) {
      case 'streak':
        return '🔥';
      case 'period':
        return '📅';
      case 'city':
        return '🏙️';
      case 'referral':
        return '👥';
      default:
        return '🎁';
    }
  };

  const getPromotionTypeText = (type: string) => {
    switch (type) {
      case 'streak':
        return 'Серия заказов';
      case 'period':
        return 'Период';
      case 'city':
        return 'Город';
      case 'referral':
        return 'Реферал';
      default:
        return type;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  if (loading) {
    return <LoadingScreen text="Загрузка акций..." />;
  }

  return (
    <SafeView style={styles.container}>
      <ScreenHeader title="Акции и бонусы" onBack={() => navigation.goBack()} />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[COLORS.primary]}
            tintColor={COLORS.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Active Promotions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Активные акции</Text>
          
          {promotions.length === 0 ? (
            <Card>
              <Text style={styles.emptyText}>Нет активных акций</Text>
            </Card>
          ) : (
            promotions.map((promotion) => (
              <Card key={promotion.id} style={styles.promotionCard}>
                <View style={styles.promotionHeader}>
                  <View
                    style={[
                      styles.promotionIcon,
                      { backgroundColor: COLORS.warning + '20' },
                    ]}
                  >
                    <Text style={styles.promotionIconEmoji}>
                      {getPromotionIcon(promotion.type)}
                    </Text>
                  </View>
                  <View style={styles.promotionInfo}>
                    <Text style={styles.promotionTitle}>{promotion.title}</Text>
                    <View style={styles.promotionMeta}>
                      <View
                        style={[
                          styles.typeBadge,
                          { backgroundColor: COLORS.info + '20' },
                        ]}
                      >
                        <Text style={styles.typeText}>
                          {getPromotionTypeText(promotion.type)}
                        </Text>
                      </View>
                      <Text style={styles.promotionBonus}>
                        +{promotion.bonus} ₽
                      </Text>
                    </View>
                  </View>
                </View>

                <Text style={styles.promotionDescription}>
                  {promotion.description}
                </Text>

                {promotion.userProgress && (
                  <View style={styles.progressSection}>
                    <View style={styles.progressHeader}>
                      <Text style={styles.progressLabel}>Прогресс</Text>
                      <Text style={styles.progressValue}>
                        {promotion.userProgress.currentProgress} /{' '}
                        {promotion.userProgress.targetProgress}
                      </Text>
                    </View>
                    <View style={styles.progressBar}>
                      <View
                        style={[
                          styles.progressFill,
                          {
                            width: `${
                              (promotion.userProgress.currentProgress /
                                promotion.userProgress.targetProgress) *
                              100
                            }%`,
                          },
                        ]}
                      />
                    </View>
                    {promotion.userProgress.isCompleted && (
                      <Text style={styles.progressCompleted}>
                        ✓ Акция завершена!
                      </Text>
                    )}
                  </View>
                )}

                {!promotion.userProgress && (
                  <Button
                    title="Участвовать"
                    onPress={() => handleJoin(promotion.id)}
                    loading={joiningId === promotion.id}
                    fullWidth
                    style={styles.joinButton}
                  />
                )}

                <Text style={styles.promotionDates}>
                  {formatDate(promotion.startDate)} — {formatDate(promotion.endDate)}
                </Text>
              </Card>
            ))
          )}
        </View>

        {/* Bonus History */}
        <Card title="История бонусов">
          {bonuses.length === 0 ? (
            <Text style={styles.emptyText}>Бонусов пока нет</Text>
          ) : (
            bonuses.map((bonus) => (
              <View key={bonus.id} style={styles.bonusItem}>
                <View style={styles.bonusInfo}>
                  <Text style={styles.bonusAmount}>+{bonus.amount} ₽</Text>
                  <Text style={styles.bonusDate}>{bonus.date}</Text>
                </View>
                <Text style={styles.bonusType}>{bonus.type}</Text>
              </View>
            ))
          )}
        </Card>
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
  section: {
    marginBottom: SPACING.l,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.m,
  },
  emptyText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
    textAlign: 'center',
    padding: SPACING.xl,
  },
  promotionCard: {
    marginBottom: SPACING.m,
  },
  promotionHeader: {
    flexDirection: 'row',
    marginBottom: SPACING.m,
  },
  promotionIcon: {
    width: 56,
    height: 56,
    borderRadius: BORDER_RADIUS.m,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  promotionIconEmoji: {
    fontSize: 28,
  },
  promotionInfo: {
    flex: 1,
  },
  promotionTitle: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  promotionMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.m,
  },
  typeBadge: {
    paddingHorizontal: SPACING.m,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.round,
  },
  typeText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.info,
    fontWeight: '600',
  },
  promotionBonus: {
    fontSize: FONT_SIZES.l,
    fontWeight: '700',
    color: COLORS.success,
  },
  promotionDescription: {
    fontSize: FONT_SIZES.s,
    color: COLORS.text,
    lineHeight: 22,
    marginBottom: SPACING.m,
  },
  progressSection: {
    marginBottom: SPACING.m,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.s,
  },
  progressLabel: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    fontWeight: '500',
  },
  progressValue: {
    fontSize: FONT_SIZES.s,
    color: COLORS.text,
    fontWeight: '600',
  },
  progressBar: {
    height: 8,
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.round,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.success,
    borderRadius: BORDER_RADIUS.round,
  },
  progressCompleted: {
    fontSize: FONT_SIZES.s,
    color: COLORS.success,
    fontWeight: '600',
    marginTop: SPACING.s,
  },
  joinButton: {
    marginTop: SPACING.m,
  },
  promotionDates: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    textAlign: 'center',
    marginTop: SPACING.s,
  },
  bonusItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.m,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  bonusInfo: {
    flex: 1,
  },
  bonusAmount: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.success,
  },
  bonusDate: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
  bonusType: {
    fontSize: FONT_SIZES.s,
    color: COLORS.text,
    fontWeight: '500',
  },
});
