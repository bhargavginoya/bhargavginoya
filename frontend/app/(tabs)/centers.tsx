import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function CentersScreen() {
  const { user, token } = useAuth();
  const [centers, setCenters] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    contact: '',
    latitude: '',
    longitude: '',
    radius: '100',
  });

  const isSuperAdmin = user?.role === 'super_admin';

  useEffect(() => {
    fetchCenters();
  }, []);

  const fetchCenters = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/centers`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCenters(response.data);
    } catch (error: any) {
      console.error('Error fetching centers:', error);
      Alert.alert('Error', 'Failed to load centers');
    }
  };

  const handleCreateCenter = async () => {
    if (!formData.name || !formData.address || !formData.contact) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }

    setLoading(true);
    try {
      const centerData = {
        name: formData.name,
        address: formData.address,
        contact: formData.contact,
        geofences: formData.latitude && formData.longitude ? [{
          name: `${formData.name} - Main Entrance`,
          latitude: parseFloat(formData.latitude),
          longitude: parseFloat(formData.longitude),
          radius: parseFloat(formData.radius),
        }] : [],
        holidays: [],
      };

      await axios.post(`${API_URL}/api/centers`, centerData, {
        headers: { Authorization: `Bearer ${token}` },
      });

      Alert.alert('Success', 'Center created successfully!');
      setShowModal(false);
      setFormData({ name: '', address: '', contact: '', latitude: '', longitude: '', radius: '100' });
      fetchCenters();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create center');
    } finally {
      setLoading(false);
    }
  };

  if (!isSuperAdmin) {
    return (
      <View style={styles.container}>
        <View style={styles.noAccessContainer}>
          <Ionicons name="business" size={64} color="#6B7280" />
          <Text style={styles.noAccessText}>Centers</Text>
          <Text style={styles.noAccessSubtext}>
            You can view centers but only Super Admin can manage them
          </Text>
        </View>
        <ScrollView style={styles.centersList}>
          {centers.map((center) => (
            <View key={center.id} style={styles.centerCard}>
              <View style={styles.centerHeader}>
                <Ionicons name="location" size={24} color="#1E3A8A" />
                <Text style={styles.centerName}>{center.name}</Text>
              </View>
              <Text style={styles.centerAddress}>{center.address}</Text>
              <Text style={styles.centerContact}>{center.contact}</Text>
              <View style={styles.centerStats}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{center.employee_count}</Text>
                  <Text style={styles.statLabel}>Employees</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{center.geofences.length}</Text>
                  <Text style={styles.statLabel}>Geofences</Text>
                </View>
              </View>
            </View>
          ))}
        </ScrollView>
      </View>
    );
  }

  return (
    <>
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Center Management</Text>
          <Text style={styles.subtitle}>Manage Gyanmanjari centers</Text>
        </View>

        <TouchableOpacity style={styles.addButton} onPress={() => setShowModal(true)}>
          <Ionicons name="add-circle" size={24} color="#FFFFFF" />
          <Text style={styles.addButtonText}>Add New Center</Text>
        </TouchableOpacity>

        <ScrollView style={styles.centersList}>
          {centers.map((center) => (
            <View key={center.id} style={styles.centerCard}>
              <View style={styles.centerHeader}>
                <Ionicons name="location" size={24} color="#1E3A8A" />
                <Text style={styles.centerName}>{center.name}</Text>
              </View>
              <Text style={styles.centerAddress}>{center.address}</Text>
              <Text style={styles.centerContact}>📞 {center.contact}</Text>
              
              <View style={styles.centerStats}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{center.employee_count}</Text>
                  <Text style={styles.statLabel}>Employees</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{center.geofences.length}</Text>
                  <Text style={styles.statLabel}>Geofences</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{center.holidays.length}</Text>
                  <Text style={styles.statLabel}>Holidays</Text>
                </View>
              </View>

              {center.geofences.length > 0 && (
                <View style={styles.geofenceList}>
                  <Text style={styles.geofenceTitle}>Geofences:</Text>
                  {center.geofences.map((gf: any, idx: number) => (
                    <View key={idx} style={styles.geofenceItem}>
                      <Ionicons name="location-outline" size={16} color="#6B7280" />
                      <Text style={styles.geofenceText}>
                        {gf.name} ({gf.radius}m radius)
                      </Text>
                    </View>
                  ))}
                </View>
              )}
            </View>
          ))}
        </ScrollView>
      </View>

      <Modal visible={showModal} animationType="slide" transparent={true}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add New Center</Text>
              <TouchableOpacity onPress={() => setShowModal(false)}>
                <Ionicons name="close" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalForm}>
              <Text style={styles.label}>Center Name *</Text>
              <TextInput
                style={styles.input}
                value={formData.name}
                onChangeText={(text) => setFormData({ ...formData, name: text })}
                placeholder="e.g., Gyanmanjari Main Branch"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Address *</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={formData.address}
                onChangeText={(text) => setFormData({ ...formData, address: text })}
                placeholder="Full address"
                multiline
                numberOfLines={3}
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Contact Number *</Text>
              <TextInput
                style={styles.input}
                value={formData.contact}
                onChangeText={(text) => setFormData({ ...formData, contact: text })}
                placeholder="+91 1234567890"
                keyboardType="phone-pad"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Latitude (Optional)</Text>
              <TextInput
                style={styles.input}
                value={formData.latitude}
                onChangeText={(text) => setFormData({ ...formData, latitude: text })}
                placeholder="28.6139"
                keyboardType="decimal-pad"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Longitude (Optional)</Text>
              <TextInput
                style={styles.input}
                value={formData.longitude}
                onChangeText={(text) => setFormData({ ...formData, longitude: text })}
                placeholder="77.2090"
                keyboardType="decimal-pad"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Geofence Radius (meters)</Text>
              <TextInput
                style={styles.input}
                value={formData.radius}
                onChangeText={(text) => setFormData({ ...formData, radius: text })}
                placeholder="100"
                keyboardType="numeric"
                placeholderTextColor="#9CA3AF"
              />

              <TouchableOpacity
                style={styles.submitButton}
                onPress={handleCreateCenter}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.submitButtonText}>Create Center</Text>
                )}
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    backgroundColor: '#1E3A8A',
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
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1E3A8A',
    marginHorizontal: 16,
    marginVertical: 16,
    paddingVertical: 16,
    borderRadius: 12,
  },
  addButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  centersList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  centerCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  centerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  centerName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginLeft: 8,
  },
  centerAddress: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 4,
  },
  centerContact: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 12,
  },
  centerStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    marginTop: 8,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E3A8A',
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
  geofenceList: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  geofenceTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  geofenceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  geofenceText: {
    fontSize: 13,
    color: '#6B7280',
    marginLeft: 8,
  },
  noAccessContainer: {
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 16,
  },
  noAccessText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 16,
  },
  noAccessSubtext: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 24,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  modalForm: {
    paddingHorizontal: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#111827',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: '#1E3A8A',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 24,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});