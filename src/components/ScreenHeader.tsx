import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../constants';

interface ScreenHeaderProps {
  title: string;
  onBack: () => void;
  right?: React.ReactNode;
}

export const ScreenHeader: React.FC<ScreenHeaderProps> = ({ title, onBack, right }) => (
  <View style={styles.container}>
    <TouchableOpacity
      onPress={onBack}
      style={styles.backButton}
      hitSlop={{ top: 10, bottom: 10, left: 10, right: 20 }}
    >
      <Text style={styles.chevron}>‹</Text>
    </TouchableOpacity>
    <Text style={styles.title} numberOfLines={1}>{title}</Text>
    <View style={styles.right}>{right ?? null}</View>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.l,
    paddingVertical: SPACING.m,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    width: 40,
    paddingBottom: 2,
  },
  chevron: {
    fontSize: 34,
    color: COLORS.primary,
    lineHeight: 36,
  },
  title: {
    flex: 1,
    fontSize: FONT_SIZES.xl,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
  },
  right: {
    width: 40,
    alignItems: 'flex-end',
  },
});
