import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { CameraView, useCameraPermissions } from 'expo-camera';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function AttendanceScreen() {
  const { user, token } = useAuth();
  const [todayStatus, setTodayStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [geofences, setGeofences] = useState<any[]>([]);
  const [currentLocation, setCurrentLocation] = useState<any>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [history, setHistory] = useState<any[]>([]);
  const cameraRef = React.useRef<any>(null);

  useEffect(() => {
    fetchTodayStatus();
    fetchGeofences();
    fetchHistory();
    requestLocationPermission();
  }, []);

  const requestLocationPermission = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Denied', 'Location permission is required for attendance');
    }
  };

  const fetchTodayStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/attendance/today-status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTodayStatus(response.data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const fetchGeofences = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/geofences`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setGeofences(response.data);
    } catch (error) {
      console.error('Error fetching geofences:', error);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/attendance/my-history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleCheckIn = async () => {
    if (geofences.length === 0) {
      Alert.alert('No Geofence', 'No geofence locations are configured. Please contact HR.');
      return;
    }

    setLoading(true);
    try {
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });
      setCurrentLocation(location.coords);

      // Show camera for selfie
      if (permission?.granted) {
        setShowCamera(true);
      } else {
        const result = await requestPermission();
        if (result.granted) {
          setShowCamera(true);
        } else {
          Alert.alert('Camera Permission', 'Camera permission is required for check-in');
        }
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to get location');
    } finally {
      setLoading(false);
    }
  };

  const handleTakeSelfie = async () => {
    if (!cameraRef.current || !currentLocation) return;

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.5,
        base64: true,
      });

      setShowCamera(false);
      setLoading(true);

      // Use the first geofence (in production, you'd select based on proximity)
      const selectedGeofence = geofences[0];

      const response = await axios.post(
        `${API_URL}/api/attendance/checkin`,
        {
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude,
          selfie_base64: photo.base64,
          geofence_id: selectedGeofence.id,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      Alert.alert('Success', 'Checked in successfully!');
      fetchTodayStatus();
      fetchHistory();
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Check-in failed';
      Alert.alert('Check-in Failed', message);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckOut = async () => {
    Alert.alert('Confirm Check Out', 'Are you sure you want to check out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Check Out',
        onPress: async () => {
          try {
            setLoading(true);
            const location = await Location.getCurrentPositionAsync({
              accuracy: Location.Accuracy.High,
            });

            await axios.post(
              `${API_URL}/api/attendance/checkout`,
              {
                latitude: location.coords.latitude,
                longitude: location.coords.longitude,
              },
              {
                headers: { Authorization: `Bearer ${token}` },
              }
            );

            Alert.alert('Success', 'Checked out successfully!');
            fetchTodayStatus();
            fetchHistory();
          } catch (error: any) {
            const message = error.response?.data?.detail || 'Check-out failed';
            Alert.alert('Error', message);
          } finally {
            setLoading(false);
          }
        },
      },
    ]);
  };

  if (showCamera) {
    return (
      <View style={styles.cameraContainer}>
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing="front"
        >
          <View style={styles.cameraOverlay}>
            <Text style={styles.cameraText}>Position your face in the frame</Text>
            <TouchableOpacity style={styles.captureButton} onPress={handleTakeSelfie}>
              <Ionicons name="camera" size={32} color="#FFFFFF" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={() => setShowCamera(false)}
            >
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </CameraView>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Attendance</Text>
        <Text style={styles.subtitle}>Manage your daily attendance</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.statusHeader}>
          <Ionicons name="today" size={24} color="#4F46E5" />
          <Text style={styles.cardTitle}>Today's Status</Text>
        </View>

        {todayStatus?.checked_in ? (
          <View style={styles.checkedInContainer}>
            <View style={styles.statusBadge}>
              <Ionicons name="checkmark-circle" size={20} color="#10B981" />
              <Text style={styles.statusBadgeText}>Checked In</Text>
            </View>
            <Text style={styles.timeDisplay}>
              {todayStatus.check_in_time
                ? new Date(todayStatus.check_in_time).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : 'N/A'}
            </Text>

            {!todayStatus.checked_out && (
              <TouchableOpacity
                style={styles.checkOutButton}
                onPress={handleCheckOut}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <>
                    <Ionicons name="exit" size={20} color="#FFFFFF" />
                    <Text style={styles.buttonText}>Check Out</Text>
                  </>
                )}
              </TouchableOpacity>
            )}

            {todayStatus.checked_out && (
              <View style={[styles.statusBadge, { backgroundColor: '#FEE2E2' }]}>
                <Ionicons name="checkmark-done" size={20} color="#EF4444" />
                <Text style={[styles.statusBadgeText, { color: '#EF4444' }]}>
                  Checked Out at{' '}
                  {new Date(todayStatus.check_out_time).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
              </View>
            )}
          </View>
        ) : (
          <View style={styles.notCheckedContainer}>
            <Ionicons name="alert-circle-outline" size={64} color="#F59E0B" />
            <Text style={styles.notCheckedText}>Not checked in yet</Text>
            <TouchableOpacity
              style={styles.checkInButton}
              onPress={handleCheckIn}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <>
                  <Ionicons name="finger-print" size={20} color="#FFFFFF" />
                  <Text style={styles.buttonText}>Check In Now</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        )}
      </View>

      <View style={styles.historySection}>
        <Text style={styles.sectionTitle}>Recent Attendance</Text>
        {history.slice(0, 5).map((record) => (
          <View key={record.id} style={styles.historyCard}>
            <View style={styles.historyHeader}>
              <Text style={styles.historyDate}>{record.date}</Text>
              <View
                style={[
                  styles.historyBadge,
                  {
                    backgroundColor:
                      record.status === 'present' ? '#D1FAE5' : '#FEE2E2',
                  },
                ]}
              >
                <Text
                  style={[
                    styles.historyBadgeText,
                    {
                      color: record.status === 'present' ? '#10B981' : '#EF4444',
                    },
                  ]}
                >
                  {record.status}
                </Text>
              </View>
            </View>
            <View style={styles.historyTimes}>
              <View style={styles.historyTime}>
                <Ionicons name="log-in" size={16} color="#6B7280" />
                <Text style={styles.historyTimeText}>
                  {new Date(record.check_in_time).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
              </View>
              {record.check_out_time && (
                <View style={styles.historyTime}>
                  <Ionicons name="log-out" size={16} color="#6B7280" />
                  <Text style={styles.historyTimeText}>
                    {new Date(record.check_out_time).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </Text>
                </View>
              )}
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    backgroundColor: '#4F46E5',
    paddingTop: 60,
    paddingBottom: 32,
    paddingHorizontal: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  subtitle: {
    fontSize: 14,
    color: '#E0E7FF',
    marginTop: 4,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    margin: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
  },
  checkedInContainer: {
    alignItems: 'center',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 12,
  },
  statusBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#10B981',
    marginLeft: 6,
  },
  timeDisplay: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#4F46E5',
    marginVertical: 16,
  },
  checkOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EF4444',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  notCheckedContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  notCheckedText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 16,
    marginBottom: 24,
  },
  checkInButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4F46E5',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  cameraContainer: {
    flex: 1,
  },
  camera: {
    flex: 1,
  },
  cameraOverlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'flex-end',
    alignItems: 'center',
    paddingBottom: 48,
  },
  cameraText: {
    fontSize: 16,
    color: '#FFFFFF',
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginBottom: 24,
  },
  captureButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#4F46E5',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 4,
    borderColor: '#FFFFFF',
  },
  cancelButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 8,
  },
  cancelText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  historySection: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  historyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  historyDate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  historyBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  historyBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  historyTimes: {
    flexDirection: 'row',
    gap: 24,
  },
  historyTime: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  historyTimeText: {
    fontSize: 14,
    color: '#6B7280',
    marginLeft: 6,
  },
});
