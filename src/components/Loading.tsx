import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet, Modal } from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '../constants';

interface LoadingProps {
  visible: boolean;
  text?: string;
  fullScreen?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({
  visible,
  text,
  fullScreen = false,
}) => {
  if (fullScreen) {
    return (
      <Modal
        visible={visible}
        transparent
        animationType="fade"
        onRequestClose={() => {}}
      >
        <View style={styles.fullScreenOverlay}>
          <View style={styles.fullScreenContent}>
            <ActivityIndicator size="large" color={COLORS.primary} />
            {text && <Text style={styles.fullScreenText}>{text}</Text>}
          </View>
        </View>
      </Modal>
    );
  }

  if (!visible) return null;

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color={COLORS.primary} />
      {text && <Text style={styles.text}>{text}</Text>}
    </View>
  );
};

export const LoadingScreen: React.FC<{ text?: string }> = ({ text }) => {
  return (
    <View style={styles.loadingScreen}>
      <View style={styles.loadingScreenContent}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        {text && <Text style={styles.loadingScreenText}>{text}</Text>}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: SPACING.l,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    marginTop: SPACING.m,
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
  },
  fullScreenOverlay: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  fullScreenContent: {
    alignItems: 'center',
  },
  fullScreenText: {
    marginTop: SPACING.m,
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
  },
  loadingScreen: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingScreenContent: {
    alignItems: 'center',
  },
  loadingScreenText: {
    marginTop: SPACING.m,
    fontSize: FONT_SIZES.l,
    color: COLORS.text,
    fontWeight: '500',
  },
});
