import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { COLORS, SPACING, BORDER_RADIUS, FONT_SIZES } from '../constants';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  fullWidth = false,
  style,
  textStyle,
  icon,
}) => {
  const getButtonStyle = (): ViewStyle[] => {
    const baseStyle: ViewStyle[] = [styles.button];

    // Variant
    switch (variant) {
      case 'secondary':
        baseStyle.push(styles.buttonSecondary);
        break;
      case 'outline':
        baseStyle.push(styles.buttonOutline);
        break;
      case 'danger':
        baseStyle.push(styles.buttonDanger);
        break;
      default:
        baseStyle.push(styles.buttonPrimary);
    }

    // Size
    switch (size) {
      case 'small':
        baseStyle.push(styles.buttonSmall);
        break;
      case 'large':
        baseStyle.push(styles.buttonLarge);
        break;
      default:
        baseStyle.push(styles.buttonMedium);
    }

    // Full width
    if (fullWidth) {
      baseStyle.push(styles.buttonFullWidth);
    }

    // Disabled
    if (disabled) {
      baseStyle.push(styles.buttonDisabled);
    }

    return baseStyle;
  };

  const getTextStyle = (): TextStyle[] => {
    const baseStyle: TextStyle[] = [styles.text];

    // Variant
    switch (variant) {
      case 'secondary':
        baseStyle.push(styles.textSecondary);
        break;
      case 'outline':
        baseStyle.push(styles.textOutline);
        break;
      case 'danger':
        baseStyle.push(styles.textDanger);
        break;
      default:
        baseStyle.push(styles.textPrimary);
    }

    // Size
    switch (size) {
      case 'small':
        baseStyle.push(styles.textSmall);
        break;
      case 'large':
        baseStyle.push(styles.textLarge);
        break;
      default:
        baseStyle.push(styles.textMedium);
    }

    // Disabled
    if (disabled) {
      baseStyle.push(styles.textDisabled);
    }

    return baseStyle;
  };

  return (
    <TouchableOpacity
      style={[...getButtonStyle(), style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'outline' ? COLORS.primary : COLORS.white} />
      ) : (
        <>
          {icon && <>{icon}</>}
          <Text style={[...getTextStyle(), textStyle]}>{title}</Text>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: BORDER_RADIUS.m,
    gap: SPACING.s,
  } as ViewStyle,
  buttonPrimary: {
    backgroundColor: COLORS.primary,
  } as ViewStyle,
  buttonSecondary: {
    backgroundColor: COLORS.accent,
  } as ViewStyle,
  buttonOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  } as ViewStyle,
  buttonDanger: {
    backgroundColor: COLORS.error,
  } as ViewStyle,
  buttonSmall: {
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.m,
  } as ViewStyle,
  buttonMedium: {
    paddingVertical: SPACING.s,
    paddingHorizontal: SPACING.l,
  } as ViewStyle,
  buttonLarge: {
    paddingVertical: SPACING.m,
    paddingHorizontal: SPACING.xl,
  } as ViewStyle,
  buttonFullWidth: {
    width: '100%',
  } as ViewStyle,
  buttonDisabled: {
    backgroundColor: COLORS.grayLight,
  } as ViewStyle,
  text: {
    fontWeight: '600',
  } as TextStyle,
  textPrimary: {
    color: COLORS.white,
  } as TextStyle,
  textSecondary: {
    color: COLORS.white,
  } as TextStyle,
  textOutline: {
    color: COLORS.primary,
  } as TextStyle,
  textDanger: {
    color: COLORS.white,
  } as TextStyle,
  textSmall: {
    fontSize: FONT_SIZES.xs,
  } as TextStyle,
  textMedium: {
    fontSize: FONT_SIZES.m,
  } as TextStyle,
  textLarge: {
    fontSize: FONT_SIZES.l,
  } as TextStyle,
  textDisabled: {
    color: COLORS.gray,
  } as TextStyle,
});
