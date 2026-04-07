import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  ViewStyle,
} from 'react-native';
import { COLORS, SPACING, BORDER_RADIUS, FONT_SIZES } from '../constants';
import { Button } from './Button';

interface ModalProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  showCloseButton?: boolean;
  style?: ViewStyle;
}

export const CustomModal: React.FC<ModalProps> = ({
  visible,
  onClose,
  title,
  children,
  footer,
  showCloseButton = true,
  style,
}) => {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={[styles.modal, style]}>
          {(title || showCloseButton) && (
            <View style={styles.header}>
              {title && <Text style={styles.title}>{title}</Text>}
              {showCloseButton && (
                <TouchableOpacity onPress={onClose} style={styles.closeButton}>
                  <Text style={styles.closeButtonText}>✕</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
          
          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {children}
          </ScrollView>
          
          {footer && <View style={styles.footer}>{footer}</View>}
        </View>
      </View>
    </Modal>
  );
};

interface ConfirmationModalProps {
  visible: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'default' | 'danger';
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  visible,
  title,
  message,
  confirmText = 'Подтвердить',
  cancelText = 'Отмена',
  onConfirm,
  onCancel,
  variant = 'default',
}) => {
  return (
    <CustomModal
      visible={visible}
      onClose={onCancel}
      title={title}
      showCloseButton={false}
      style={styles.confirmationModal}
    >
      <Text style={styles.message}>{message}</Text>
      
      <View style={styles.buttons}>
        <Button
          title={cancelText}
          onPress={onCancel}
          variant="outline"
          style={styles.button}
        />
        <Button
          title={confirmText}
          onPress={onConfirm}
          variant={variant === 'danger' ? 'danger' : 'primary'}
          style={styles.button}
        />
      </View>
    </CustomModal>
  );
};

interface InfoModalProps {
  visible: boolean;
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  actionText?: string;
  onAction?: () => void;
}

export const InfoModal: React.FC<InfoModalProps> = ({
  visible,
  title,
  children,
  onClose,
  actionText,
  onAction,
}) => {
  return (
    <CustomModal
      visible={visible}
      onClose={onClose}
      title={title}
      footer={
        <View style={styles.infoModalFooter}>
          {actionText && onAction && (
            <Button
              title={actionText}
              onPress={onAction}
              fullWidth
              style={styles.actionButton}
            />
          )}
          <Button
            title="Закрыть"
            onPress={onClose}
            variant="outline"
            fullWidth
          />
        </View>
      }
    >
      {children}
    </CustomModal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.l,
  },
  modal: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.xl,
    width: '100%',
    maxHeight: Dimensions.get('window').height * 0.8,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.m,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  title: {
    fontSize: FONT_SIZES.l,
    fontWeight: '600',
    color: COLORS.text,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: BORDER_RADIUS.round,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeButtonText: {
    fontSize: FONT_SIZES.m,
    color: COLORS.gray,
  },
  content: {
    padding: SPACING.m,
    maxHeight: 400,
  },
  footer: {
    padding: SPACING.m,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  message: {
    fontSize: FONT_SIZES.m,
    color: COLORS.text,
    lineHeight: 22,
  },
  buttons: {
    flexDirection: 'row',
    gap: SPACING.m,
    marginTop: SPACING.l,
  },
  button: {
    flex: 1,
  },
  confirmationModal: {
    maxWidth: 400,
  },
  infoModalFooter: {
    gap: SPACING.m,
  },
  actionButton: {
    marginBottom: SPACING.s,
  },
});
