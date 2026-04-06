import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { COLORS, SPACING, BORDER_RADIUS, FONT_SIZES } from '../constants';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  onPress?: () => void;
  style?: ViewStyle;
  padding?: 'none' | 'small' | 'medium' | 'large';
  variant?: 'default' | 'outlined' | 'filled';
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  onPress,
  style,
  padding = 'medium',
  variant = 'default',
}) => {
  const getPadding = (): ViewStyle => {
    switch (padding) {
      case 'none':
        return { padding: 0 };
      case 'small':
        return { padding: SPACING.m };
      case 'large':
        return { padding: SPACING.xl };
      default:
        return { padding: SPACING.m };
    }
  };

  const getVariant = (): ViewStyle => {
    switch (variant) {
      case 'outlined':
        return { borderWidth: 1, borderColor: COLORS.border };
      case 'filled':
        return { backgroundColor: COLORS.background };
      default:
        return {
          shadowColor: COLORS.black,
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.1,
          shadowRadius: 4,
          elevation: 3,
        };
    }
  };

  return (
    <View
      style={[
        styles.card,
        getPadding(),
        getVariant(),
        style,
      ]}
    >
      {(title || subtitle) && (
        <View style={styles.header}>
          {title && <Text style={styles.title}>{title}</Text>}
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        </View>
      )}
      {children}
    </View>
  );
};

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: string;
  color?: string;
  onPress?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  color = COLORS.primary,
  onPress,
}) => {
  return (
    <View style={[styles.statCard, onPress && styles.statCardPressable]}>
      {icon && (
        <View style={[styles.statIcon, { backgroundColor: color + '20' }]}>
          <Text style={styles.statIconEmoji}>{icon}</Text>
        </View>
      )}
      <View style={styles.statContent}>
        <Text style={styles.statValue}>{value}</Text>
        <Text style={styles.statLabel}>{label}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.l,
    marginVertical: SPACING.s,
  },
  header: {
    marginBottom: SPACING.m,
  },
  title: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  subtitle: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
  },
  statCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.m,
    padding: SPACING.m,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statCardPressable: {
    opacity: 0.9,
  },
  statIcon: {
    width: 48,
    height: 48,
    borderRadius: BORDER_RADIUS.m,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  statIconEmoji: {
    fontSize: 24,
  },
  statContent: {
    flex: 1,
  },
  statValue: {
    fontSize: FONT_SIZES.xl,
    fontWeight: '700',
    color: COLORS.text,
  },
  statLabel: {
    fontSize: FONT_SIZES.s,
    color: COLORS.gray,
    marginTop: SPACING.xs,
  },
});
