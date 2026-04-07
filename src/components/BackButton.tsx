import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { COLORS, SPACING } from '../constants';

interface BackButtonProps {
  onPress: () => void;
}

export const BackButton: React.FC<BackButtonProps> = ({ onPress }) => (
  <TouchableOpacity
    onPress={onPress}
    style={styles.button}
    hitSlop={{ top: 10, bottom: 10, left: 10, right: 20 }}
  >
    <Text style={styles.chevron}>‹</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  button: {
    alignSelf: 'flex-start',
    paddingRight: SPACING.m,
    paddingBottom: SPACING.xs,
  },
  chevron: {
    fontSize: 34,
    color: COLORS.primary,
    lineHeight: 36,
  },
});
