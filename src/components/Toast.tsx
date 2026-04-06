import React, { useEffect, useCallback, useState } from 'react';
import { View, Text, StyleSheet, Animated, Dimensions } from 'react-native';
import { COLORS, SPACING, BORDER_RADIUS, FONT_SIZES } from '../constants';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastProps {
  message: string;
  type?: ToastType;
  visible: boolean;
  onHide: () => void;
  duration?: number;
}

export const Toast: React.FC<ToastProps> = ({
  message,
  type = 'info',
  visible,
  onHide,
  duration = 3000,
}) => {
  const opacity = React.useRef(new Animated.Value(0)).current;
  const translateY = React.useRef(new Animated.Value(-100)).current;

  const getToastStyle = () => {
    switch (type) {
      case 'success':
        return styles.toastSuccess;
      case 'error':
        return styles.toastError;
      case 'warning':
        return styles.toastWarning;
      default:
        return styles.toastInfo;
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      default:
        return 'ℹ';
    }
  };

  const showAnimation = useCallback(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(translateY, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();

      if (duration > 0) {
        setTimeout(() => {
          hideAnimation();
        }, duration);
      }
    }
  }, [visible, duration, opacity, translateY]);

  const hideAnimation = useCallback(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: -100,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onHide();
    });
  }, [onHide, opacity, translateY]);

  useEffect(() => {
    if (visible) {
      showAnimation();
    }
  }, [visible, showAnimation]);

  if (!visible) return null;

  return (
    <Animated.View
      style={[
        styles.container,
        getToastStyle(),
        {
          opacity,
          transform: [{ translateY }],
        },
      ]}
    >
      <View style={styles.icon}>
        <Text style={styles.iconText}>{getIcon()}</Text>
      </View>
      <Text style={styles.message}>{message}</Text>
    </Animated.View>
  );
};

interface ToastContainerProps {
  toasts: Array<{
    id: string;
    message: string;
    type: ToastType;
  }>;
  onRemove: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
  return (
    <View style={styles.toastContainer}>
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          visible={true}
          onHide={() => onRemove(toast.id)}
          duration={3000}
        />
      ))}
    </View>
  );
};

// Hook for showing toasts
export const useToast = () => {
  const [toasts, setToasts] = React.useState<Array<{ id: string; message: string; type: ToastType }>>([]);

  const addToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 3000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const success = useCallback((message: string) => addToast(message, 'success'), [addToast]);
  const error = useCallback((message: string) => addToast(message, 'error'), [addToast]);
  const info = useCallback((message: string) => addToast(message, 'info'), [addToast]);
  const warning = useCallback((message: string) => addToast(message, 'warning'), [addToast]);

  return {
    toasts,
    removeToast,
    success,
    error,
    info,
    warning,
    ToastContainer: () => <ToastContainer toasts={toasts} onRemove={removeToast} />,
  };
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.m,
    paddingVertical: SPACING.m,
    borderRadius: BORDER_RADIUS.m,
    marginHorizontal: SPACING.m,
    marginBottom: SPACING.s,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  toastSuccess: {
    backgroundColor: COLORS.success,
  },
  toastError: {
    backgroundColor: COLORS.error,
  },
  toastInfo: {
    backgroundColor: COLORS.info,
  },
  toastWarning: {
    backgroundColor: COLORS.warning,
  },
  icon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.m,
  },
  iconText: {
    fontSize: FONT_SIZES.l,
    color: COLORS.white,
    fontWeight: '700',
  },
  message: {
    flex: 1,
    fontSize: FONT_SIZES.m,
    color: COLORS.white,
    fontWeight: '500',
  },
  toastContainer: {
    position: 'absolute',
    top: 40,
    left: 0,
    right: 0,
    zIndex: 9999,
  },
});
