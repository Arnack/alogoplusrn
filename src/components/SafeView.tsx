import React from 'react';
import { View, ViewStyle } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

interface SafeViewProps {
  children: React.ReactNode;
  style?: ViewStyle;
  edges?: ('top' | 'bottom' | 'left' | 'right')[];
}

export const SafeView: React.FC<SafeViewProps> = ({ children, style, edges = ['top', 'bottom'] }) => {
  const insets = useSafeAreaInsets();

  const appliedStyle: ViewStyle = {
    flex: 1,
    paddingTop: edges.includes('top') ? insets.top : 0,
    paddingBottom: edges.includes('bottom') ? insets.bottom : 0,
    paddingLeft: edges.includes('left') ? insets.left : 0,
    paddingRight: edges.includes('right') ? insets.right : 0,
    ...style,
  };

  return <View style={appliedStyle}>{children}</View>;
};
