import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import FaceFrameCamera from './FaceFrameCamera';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface FirstTimeSetupProps {
  visible: boolean;
  onComplete: () => void;
  token: string;
  userId: string;
}

export default function FirstTimeSetup({
  visible,
  onComplete,
  token,
  userId,
}: FirstTimeSetupProps) {
  const [showCamera, setShowCamera] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [step, setStep] = useState(1);

  const handlePhotoCapture = (photo: any) => {
    setCapturedPhoto(photo);
    setShowCamera(false);
    setStep(2);
  };

  const handleRetake = () => {
    setCapturedPhoto(null);
    setStep(1);
    setShowCamera(true);
  };

  const handleConfirm = async () => {
    if (!capturedPhoto) return;

    setUploading(true);
    try {
      // Save face configuration
      const faceData = {
        user_id: userId,
        face_image_base64: capturedPhoto.base64,
        configured_at: new Date().toISOString(),
      };

      // Store in backend (you'll need to add this endpoint)
      await axios.post(
        `${API_URL}/api/users/configure-face`,
        faceData,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Mark as configured in local storage
      await AsyncStorage.setItem('face_configured', 'true');

      Alert.alert('Success', 'Face configuration completed! You can now use face recognition for attendance.');
      onComplete();
    } catch (error: any) {
      console.error('Error saving face config:', error);
      Alert.alert('Error', 'Failed to save face configuration. You can set it up later from Profile.');
      onComplete(); // Allow them to proceed anyway
    } finally {
      setUploading(false);
    }
  };

  const handleSkip = async () => {
    Alert.alert(
      'Skip Face Configuration?',
      'You can set this up later from your Profile settings.',
      [
        { text: 'Go Back', style: 'cancel' },
        {
          text: 'Skip',
          onPress: async () => {
            await AsyncStorage.setItem('face_configured', 'skipped');
            onComplete();
          },
        },
      ]
    );
  };

  return (
    <>
      <Modal visible={visible && !showCamera} animationType="slide" transparent={true}>
        <View style={styles.container}>
          <View style={styles.content}>
            {step === 1 ? (
              // Step 1: Introduction
              <>
                <View style={styles.iconContainer}>
                  <Ionicons name="scan" size={64} color="#1E3A8A" />
                </View>
                <Text style={styles.title}>Face Configuration</Text>
                <Text style={styles.subtitle}>
                  Set up face recognition for quick and secure attendance marking
                </Text>

                <View style={styles.benefitsContainer}>
                  <View style={styles.benefitItem}>
                    <Ionicons name="flash" size={24} color="#10B981" />
                    <Text style={styles.benefitText}>Faster check-in</Text>
                  </View>
                  <View style={styles.benefitItem}>
                    <Ionicons name="shield-checkmark" size={24} color="#10B981" />
                    <Text style={styles.benefitText}>Secure verification</Text>
                  </View>
                  <View style={styles.benefitItem}>
                    <Ionicons name="person" size={24} color="#10B981" />
                    <Text style={styles.benefitText}>Contactless</Text>
                  </View>
                </View>

                <TouchableOpacity
                  style={styles.primaryButton}
                  onPress={() => setShowCamera(true)}
                >
                  <Text style={styles.primaryButtonText}>Set Up Now</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
                  <Text style={styles.skipButtonText}>Skip for now</Text>
                </TouchableOpacity>
              </>
            ) : (
              // Step 2: Review captured photo
              <>
                <Text style={styles.title}>Review Your Photo</Text>
                <Text style={styles.subtitle}>Make sure your face is clearly visible</Text>

                {capturedPhoto && (
                  <View style={styles.photoPreview}>
                    <Image
                      source={{ uri: capturedPhoto.uri }}
                      style={styles.previewImage}
                    />
                  </View>
                )}

                <View style={styles.buttonRow}>
                  <TouchableOpacity
                    style={styles.secondaryButton}
                    onPress={handleRetake}
                    disabled={uploading}
                  >
                    <Ionicons name="camera-reverse" size={20} color="#1E3A8A" />
                    <Text style={styles.secondaryButtonText}>Retake</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.primaryButton, styles.confirmButton]}
                    onPress={handleConfirm}
                    disabled={uploading}
                  >
                    {uploading ? (
                      <ActivityIndicator color="#FFFFFF" />
                    ) : (
                      <>
                        <Ionicons name="checkmark" size={20} color="#FFFFFF" />
                        <Text style={styles.primaryButtonText}>Confirm</Text>
                      </>
                    )}
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>

      <FaceFrameCamera
        visible={showCamera}
        onClose={() => setShowCamera(false)}
        onCapture={handlePhotoCapture}
      />
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 32,
    width: '90%',
    maxWidth: 400,
    alignItems: 'center',
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#EFF6FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 32,
  },
  benefitsContainer: {
    width: '100%',
    marginBottom: 32,
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  benefitText: {
    fontSize: 16,
    color: '#374151',
    marginLeft: 12,
  },
  primaryButton: {
    backgroundColor: '#1E3A8A',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  skipButton: {
    paddingVertical: 16,
    marginTop: 16,
  },
  skipButtonText: {
    color: '#6B7280',
    fontSize: 14,
  },
  photoPreview: {
    width: 200,
    height: 200,
    borderRadius: 100,
    overflow: 'hidden',
    marginBottom: 32,
    borderWidth: 4,
    borderColor: '#10B981',
  },
  previewImage: {
    width: '100%',
    height: '100%',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: '#EFF6FF',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  secondaryButtonText: {
    color: '#1E3A8A',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  confirmButton: {
    flex: 1,
  },
});