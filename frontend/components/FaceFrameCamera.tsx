import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Modal,
  Dimensions,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import Svg, { Circle, Rect } from 'react-native-svg';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface FaceFrameCameraProps {
  visible: boolean;
  onClose: () => void;
  onCapture: (photo: any) => void;
  isCheckout?: boolean;
}

export default function FaceFrameCamera({
  visible,
  onClose,
  onCapture,
  isCheckout = false,
}: FaceFrameCameraProps) {
  const cameraRef = useRef<any>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [capturing, setCapturing] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const [showCountdown, setShowCountdown] = useState(false);

  useEffect(() => {
    if (visible && !permission?.granted) {
      requestPermission();
    }
  }, [visible]);

  useEffect(() => {
    if (showCountdown && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else if (showCountdown && countdown === 0) {
      takePicture();
    }
  }, [countdown, showCountdown]);

  const startCapture = () => {
    setShowCountdown(true);
    setCountdown(3);
  };

  const takePicture = async () => {
    if (!cameraRef.current) return;

    try {
      setCapturing(true);
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.7,
        base64: true,
      });

      onCapture(photo);
      setShowCountdown(false);
      setCountdown(3);
    } catch (error) {
      console.error('Error taking picture:', error);
      Alert.alert('Error', 'Failed to capture photo');
    } finally {
      setCapturing(false);
    }
  };

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <Modal visible={visible} animationType="slide">
        <View style={styles.permissionContainer}>
          <Ionicons name="camera-outline" size={64} color="#9CA3AF" />
          <Text style={styles.permissionText}>Camera permission required</Text>
          <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
            <Text style={styles.permissionButtonText}>Grant Permission</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.cancelButton} onPress={onClose}>
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </Modal>
    );
  }

  return (
    <Modal visible={visible} animationType="slide">
      <View style={styles.container}>
        <CameraView ref={cameraRef} style={styles.camera} facing="front">
          {/* Face Frame Overlay */}
          <Svg height={SCREEN_HEIGHT} width={SCREEN_WIDTH} style={styles.overlay}>
            {/* Dark overlay around face frame */}
            <Rect x="0" y="0" width={SCREEN_WIDTH} height={SCREEN_HEIGHT} fill="rgba(0,0,0,0.6)" />
            
            {/* Clear center oval for face */}
            <Circle
              cx={SCREEN_WIDTH / 2}
              cy={SCREEN_HEIGHT / 2 - 50}
              r="140"
              fill="transparent"
              stroke="#10B981"
              strokeWidth="4"
              strokeDasharray="10,5"
            />
            
            {/* Corner guides */}
            <Rect
              x={SCREEN_WIDTH / 2 - 140}
              y={SCREEN_HEIGHT / 2 - 190}
              width="30"
              height="4"
              fill="#10B981"
            />
            <Rect
              x={SCREEN_WIDTH / 2 - 140}
              y={SCREEN_HEIGHT / 2 - 190}
              width="4"
              height="30"
              fill="#10B981"
            />
            
            <Rect
              x={SCREEN_WIDTH / 2 + 110}
              y={SCREEN_HEIGHT / 2 - 190}
              width="30"
              height="4"
              fill="#10B981"
            />
            <Rect
              x={SCREEN_WIDTH / 2 + 136}
              y={SCREEN_HEIGHT / 2 - 190}
              width="4"
              height="30"
              fill="#10B981"
            />
          </Svg>

          <View style={styles.topBar}>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Ionicons name="close" size={32} color="#FFFFFF" />
            </TouchableOpacity>
          </View>

          <View style={styles.instructions}>
            <View style={styles.instructionBubble}>
              <Text style={styles.instructionText}>
                {isCheckout ? 'Capture selfie for checkout' : 'Align your face within the frame'}
              </Text>
              <Text style={styles.instructionSubtext}>Keep your face clearly visible</Text>
            </View>
          </View>

          {showCountdown && (
            <View style={styles.countdownContainer}>
              <Text style={styles.countdownText}>{countdown}</Text>
            </View>
          )}

          <View style={styles.bottomBar}>
            <TouchableOpacity
              style={[styles.captureButton, capturing && styles.captureButtonDisabled]}
              onPress={startCapture}
              disabled={capturing || showCountdown}
            >
              {capturing ? (
                <ActivityIndicator color="#FFFFFF" size="large" />
              ) : (
                <View style={styles.captureButtonInner}>
                  <Ionicons name="camera" size={32} color="#FFFFFF" />
                </View>
              )}
            </TouchableOpacity>
          </View>
        </CameraView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  topBar: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
  },
  closeButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  instructions: {
    position: 'absolute',
    top: SCREEN_HEIGHT / 2 + 120,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  instructionBubble: {
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  instructionText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
  instructionSubtext: {
    color: '#D1D5DB',
    fontSize: 13,
    marginTop: 4,
    textAlign: 'center',
  },
  countdownContainer: {
    position: 'absolute',
    top: SCREEN_HEIGHT / 2 - 50,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  countdownText: {
    fontSize: 120,
    fontWeight: 'bold',
    color: '#10B981',
    textShadowColor: '#000',
    textShadowOffset: { width: 0, height: 4 },
    textShadowRadius: 10,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 50,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#10B981',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 4,
    borderColor: '#FFFFFF',
  },
  captureButtonDisabled: {
    opacity: 0.5,
  },
  captureButtonInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#10B981',
    alignItems: 'center',
    justifyContent: 'center',
  },
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F9FAFB',
    padding: 32,
  },
  permissionText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginTop: 16,
    marginBottom: 32,
    textAlign: 'center',
  },
  permissionButton: {
    backgroundColor: '#1E3A8A',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  permissionButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  cancelButton: {
    paddingVertical: 12,
  },
  cancelButtonText: {
    color: '#6B7280',
    fontSize: 16,
  },
});