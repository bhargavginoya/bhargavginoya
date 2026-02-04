import React, { useState, useEffect } from 'react';
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
  Platform,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { format } from 'date-fns';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function LeavesScreen() {
  const { user, token } = useAuth();
  const [leaves, setLeaves] = useState<any[]>([]);
  const [balance, setBalance] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    leave_type: 'casual',
    start_date: '',
    end_date: '',
    days_count: '',
    reason: '',
  });

  useEffect(() => {
    fetchLeaves();
    fetchBalance();
  }, []);

  const fetchLeaves = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/leaves/my-leaves`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setLeaves(response.data);
    } catch (error) {
      console.error('Error fetching leaves:', error);
    }
  };

  const fetchBalance = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/leaves/balance`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setBalance(response.data);
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  const handleApplyLeave = async () => {
    if (!formData.start_date || !formData.end_date || !formData.days_count || !formData.reason) {
      Alert.alert('Error', 'Please fill all fields');
      return;
    }

    setLoading(true);
    try {
      await axios.post(
        `${API_URL}/api/leaves/apply`,
        {
          ...formData,
          days_count: parseFloat(formData.days_count),
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      Alert.alert('Success', 'Leave application submitted successfully!');
      setShowModal(false);
      setFormData({
        leave_type: 'casual',
        start_date: '',
        end_date: '',
        days_count: '',
        reason: '',
      });
      fetchLeaves();
      fetchBalance();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to apply leave';
      Alert.alert('Error', message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return { bg: '#D1FAE5', text: '#10B981' };
      case 'rejected':
        return { bg: '#FEE2E2', text: '#EF4444' };
      default:
        return { bg: '#FEF3C7', text: '#F59E0B' };
    }
  };

  return (
    <>
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Leave Management</Text>
          <Text style={styles.subtitle}>Apply and track your leaves</Text>
        </View>

        <View style={styles.balanceCard}>
          <Text style={styles.balanceTitle}>Leave Balance</Text>
          <View style={styles.balanceGrid}>
            <View style={styles.balanceItem}>
              <Text style={styles.balanceCount}>{balance?.sick_balance || 0}</Text>
              <Text style={styles.balanceLabel}>Sick</Text>
            </View>
            <View style={styles.balanceItem}>
              <Text style={styles.balanceCount}>{balance?.casual_balance || 0}</Text>
              <Text style={styles.balanceLabel}>Casual</Text>
            </View>
            <View style={styles.balanceItem}>
              <Text style={styles.balanceCount}>{balance?.earned_balance || 0}</Text>
              <Text style={styles.balanceLabel}>Earned</Text>
            </View>
          </View>
        </View>

        <TouchableOpacity style={styles.applyButton} onPress={() => setShowModal(true)}>
          <Ionicons name="add-circle" size={24} color="#FFFFFF" />
          <Text style={styles.applyButtonText}>Apply for Leave</Text>
        </TouchableOpacity>

        <View style={styles.historySection}>
          <Text style={styles.sectionTitle}>Leave History</Text>
          {leaves.map((leave) => {
            const statusColors = getStatusColor(leave.status);
            return (
              <View key={leave.id} style={styles.leaveCard}>
                <View style={styles.leaveHeader}>
                  <View style={styles.leaveType}>
                    <Ionicons name="calendar" size={20} color="#4F46E5" />
                    <Text style={styles.leaveTypeText}>{leave.leave_type}</Text>
                  </View>
                  <View
                    style={[
                      styles.statusBadge,
                      { backgroundColor: statusColors.bg },
                    ]}
                  >
                    <Text style={[styles.statusText, { color: statusColors.text }]}>
                      {leave.status}
                    </Text>
                  </View>
                </View>
                <Text style={styles.leaveDates}>
                  {leave.start_date} to {leave.end_date} ({leave.days_count} days)
                </Text>
                <Text style={styles.leaveReason}>{leave.reason}</Text>
                {leave.remarks && (
                  <View style={styles.remarksContainer}>
                    <Ionicons name="chatbox-outline" size={16} color="#6B7280" />
                    <Text style={styles.remarksText}>{leave.remarks}</Text>
                  </View>
                )}
                <Text style={styles.leaveDate}>
                  Applied on {new Date(leave.applied_at).toLocaleDateString()}
                </Text>
              </View>
            );
          })}
        </View>
      </ScrollView>

      <Modal visible={showModal} animationType="slide" transparent={true}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Apply for Leave</Text>
              <TouchableOpacity onPress={() => setShowModal(false)}>
                <Ionicons name="close" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalForm}>
              <Text style={styles.label}>Leave Type</Text>
              <View style={styles.radioGroup}>
                {['casual', 'sick', 'earned'].map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.radioButton,
                      formData.leave_type === type && styles.radioButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, leave_type: type })}
                  >
                    <Text
                      style={[
                        styles.radioText,
                        formData.leave_type === type && styles.radioTextActive,
                      ]}
                    >
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.label}>Start Date (YYYY-MM-DD)</Text>
              <TextInput
                style={styles.input}
                value={formData.start_date}
                onChangeText={(text) => setFormData({ ...formData, start_date: text })}
                placeholder="2025-01-15"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>End Date (YYYY-MM-DD)</Text>
              <TextInput
                style={styles.input}
                value={formData.end_date}
                onChangeText={(text) => setFormData({ ...formData, end_date: text })}
                placeholder="2025-01-17"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Number of Days</Text>
              <TextInput
                style={styles.input}
                value={formData.days_count}
                onChangeText={(text) => setFormData({ ...formData, days_count: text })}
                placeholder="3"
                keyboardType="numeric"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Reason</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={formData.reason}
                onChangeText={(text) => setFormData({ ...formData, reason: text })}
                placeholder="Enter reason for leave"
                multiline
                numberOfLines={4}
                placeholderTextColor="#9CA3AF"
              />

              <TouchableOpacity
                style={styles.submitButton}
                onPress={handleApplyLeave}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.submitButtonText}>Submit Application</Text>
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
  balanceCard: {
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
  balanceTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  balanceGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  balanceItem: {
    alignItems: 'center',
    flex: 1,
  },
  balanceCount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4F46E5',
  },
  balanceLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
  applyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4F46E5',
    marginHorizontal: 16,
    paddingVertical: 16,
    borderRadius: 12,
    marginBottom: 24,
  },
  applyButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  historySection: {
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  leaveCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  leaveHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  leaveType: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  leaveTypeText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
    textTransform: 'capitalize',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  leaveDates: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  leaveReason: {
    fontSize: 14,
    color: '#374151',
    marginBottom: 8,
  },
  remarksContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F9FAFB',
    padding: 8,
    borderRadius: 8,
    marginBottom: 8,
  },
  remarksText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 6,
    flex: 1,
  },
  leaveDate: {
    fontSize: 12,
    color: '#9CA3AF',
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
  radioGroup: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  radioButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  radioButtonActive: {
    backgroundColor: '#4F46E5',
    borderColor: '#4F46E5',
  },
  radioText: {
    fontSize: 14,
    color: '#6B7280',
  },
  radioTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
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
    height: 100,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: '#4F46E5',
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
