import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  TextInput,
  Modal,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function AdminScreen() {
  const { user, token } = useAuth();
  const [users, setUsers] = useState<any[]>([]);
  const [pendingLeaves, setPendingLeaves] = useState<any[]>([]);
  const [todayAttendance, setTodayAttendance] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [showGeofenceModal, setShowGeofenceModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [geofenceData, setGeofenceData] = useState({
    name: '',
    latitude: '',
    longitude: '',
    radius: '100',
    address: '',
  });

  // Check if user has admin privileges
  const isAdmin = user?.role === 'super_admin' || user?.role === 'hr_manager';
  const isSuperAdmin = user?.role === 'super_admin';

  useEffect(() => {
    if (isAdmin) {
      fetchData();
    }
  }, []);

  const fetchData = async () => {
    try {
      const [usersRes, leavesRes, attendanceRes] = await Promise.all([
        axios.get(`${API_URL}/api/admin/users`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_URL}/api/leaves/pending`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_URL}/api/admin/attendance/all`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setUsers(usersRes.data);
      setPendingLeaves(leavesRes.data);
      setTodayAttendance(attendanceRes.data);
    } catch (error: any) {
      console.error('Error fetching admin data:', error);
      if (error.response?.status === 403) {
        Alert.alert('Access Denied', 'You do not have admin privileges');
      }
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handleApproveLeave = async (leaveId: string, status: string) => {
    try {
      await axios.post(
        `${API_URL}/api/leaves/approve`,
        { leave_id: leaveId, status, remarks: `${status} by ${user?.full_name}` },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      Alert.alert('Success', `Leave ${status} successfully`);
      fetchData();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to process leave');
    }
  };

  const handleCreateGeofence = async () => {
    if (!geofenceData.name || !geofenceData.latitude || !geofenceData.longitude) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }

    setLoading(true);
    try {
      await axios.post(
        `${API_URL}/api/geofences`,
        {
          name: geofenceData.name,
          latitude: parseFloat(geofenceData.latitude),
          longitude: parseFloat(geofenceData.longitude),
          radius: parseFloat(geofenceData.radius),
          address: geofenceData.address,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      Alert.alert('Success', 'Geofence created successfully');
      setShowGeofenceModal(false);
      setGeofenceData({ name: '', latitude: '', longitude: '', radius: '100', address: '' });
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create geofence');
    } finally {
      setLoading(false);
    }
  };

  if (!isAdmin) {
    return (
      <View style={styles.container}>
        <View style={styles.noAccessContainer}>
          <Ionicons name="lock-closed" size={64} color="#EF4444" />
          <Text style={styles.noAccessText}>Access Denied</Text>
          <Text style={styles.noAccessSubtext}>
            You need admin privileges to access this section
          </Text>
        </View>
      </View>
    );
  }

  return (
    <>
      <ScrollView
        style={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <View style={styles.header}>
          <Text style={styles.title}>{isSuperAdmin ? 'Super Admin' : 'Admin'} Panel</Text>
          <Text style={styles.subtitle}>Manage your organization</Text>
        </View>

        {/* Stats Cards */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Ionicons name="people" size={32} color="#4F46E5" />
            <Text style={styles.statNumber}>{users.length}</Text>
            <Text style={styles.statLabel}>Total Users</Text>
          </View>
          <View style={styles.statCard}>
            <Ionicons name="calendar" size={32} color="#F59E0B" />
            <Text style={styles.statNumber}>{pendingLeaves.length}</Text>
            <Text style={styles.statLabel}>Pending Leaves</Text>
          </View>
          <View style={styles.statCard}>
            <Ionicons name="checkmark-circle" size={32} color="#10B981" />
            <Text style={styles.statNumber}>{todayAttendance.length}</Text>
            <Text style={styles.statLabel}>Present Today</Text>
          </View>
        </View>

        {/* Super Admin Only: Geofence Management */}
        {isSuperAdmin && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Geofence Management</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => setShowGeofenceModal(true)}
              >
                <Ionicons name="add" size={20} color="#FFFFFF" />
                <Text style={styles.addButtonText}>Add Location</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Pending Leave Approvals */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Pending Leave Approvals</Text>
          {pendingLeaves.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="checkmark-done-circle" size={48} color="#10B981" />
              <Text style={styles.emptyText}>No pending leaves</Text>
            </View>
          ) : (
            pendingLeaves.map((leave) => (
              <View key={leave.id} style={styles.leaveCard}>
                <View style={styles.leaveHeader}>
                  <Text style={styles.leaveName}>{leave.user_name}</Text>
                  <View style={styles.leaveTypeBadge}>
                    <Text style={styles.leaveTypeText}>{leave.leave_type}</Text>
                  </View>
                </View>
                <Text style={styles.leaveDates}>
                  {leave.start_date} to {leave.end_date} ({leave.days_count} days)
                </Text>
                <Text style={styles.leaveReason}>{leave.reason}</Text>
                <View style={styles.leaveActions}>
                  <TouchableOpacity
                    style={styles.approveButton}
                    onPress={() => handleApproveLeave(leave.id, 'approved')}
                  >
                    <Ionicons name="checkmark" size={20} color="#FFFFFF" />
                    <Text style={styles.actionButtonText}>Approve</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.rejectButton}
                    onPress={() => handleApproveLeave(leave.id, 'rejected')}
                  >
                    <Ionicons name="close" size={20} color="#FFFFFF" />
                    <Text style={styles.actionButtonText}>Reject</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))
          )}
        </View>

        {/* Today's Attendance */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Today's Attendance</Text>
          {todayAttendance.map((record) => (
            <View key={record.id} style={styles.attendanceCard}>
              <View style={styles.attendanceHeader}>
                <Ionicons name="person" size={24} color="#4F46E5" />
                <Text style={styles.attendanceName}>{record.user_name}</Text>
              </View>
              <View style={styles.attendanceTime}>
                <Ionicons name="time" size={16} color="#6B7280" />
                <Text style={styles.attendanceTimeText}>
                  Check-in: {new Date(record.check_in_time).toLocaleTimeString()}
                </Text>
              </View>
              {record.check_out_time && (
                <View style={styles.attendanceTime}>
                  <Ionicons name="exit" size={16} color="#6B7280" />
                  <Text style={styles.attendanceTimeText}>
                    Check-out: {new Date(record.check_out_time).toLocaleTimeString()}
                  </Text>
                </View>
              )}
            </View>
          ))}
        </View>

        {/* All Users */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>All Users</Text>
          {users.map((u) => (
            <View key={u.id} style={styles.userCard}>
              <View style={styles.userInfo}>
                <View style={styles.userAvatar}>
                  <Ionicons name="person" size={24} color="#4F46E5" />
                </View>
                <View style={styles.userDetails}>
                  <Text style={styles.userName}>{u.full_name}</Text>
                  <Text style={styles.userEmail}>{u.email}</Text>
                  <Text style={styles.userRole}>{u.employee_id} • {u.role}</Text>
                </View>
              </View>
              <View
                style={[
                  styles.statusBadge,
                  { backgroundColor: u.is_active ? '#D1FAE5' : '#FEE2E2' },
                ]}
              >
                <Text
                  style={[
                    styles.statusText,
                    { color: u.is_active ? '#10B981' : '#EF4444' },
                  ]}
                >
                  {u.is_active ? 'Active' : 'Inactive'}
                </Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>

      {/* Geofence Modal */}
      <Modal visible={showGeofenceModal} animationType="slide" transparent={true}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Geofence Location</Text>
              <TouchableOpacity onPress={() => setShowGeofenceModal(false)}>
                <Ionicons name="close" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalForm}>
              <Text style={styles.label}>Location Name *</Text>
              <TextInput
                style={styles.input}
                value={geofenceData.name}
                onChangeText={(text) => setGeofenceData({ ...geofenceData, name: text })}
                placeholder="e.g., Main Office, Branch Office"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Latitude *</Text>
              <TextInput
                style={styles.input}
                value={geofenceData.latitude}
                onChangeText={(text) => setGeofenceData({ ...geofenceData, latitude: text })}
                placeholder="28.6139"
                keyboardType="decimal-pad"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Longitude *</Text>
              <TextInput
                style={styles.input}
                value={geofenceData.longitude}
                onChangeText={(text) => setGeofenceData({ ...geofenceData, longitude: text })}
                placeholder="77.2090"
                keyboardType="decimal-pad"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Radius (meters) *</Text>
              <TextInput
                style={styles.input}
                value={geofenceData.radius}
                onChangeText={(text) => setGeofenceData({ ...geofenceData, radius: text })}
                placeholder="100"
                keyboardType="numeric"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.label}>Address</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={geofenceData.address}
                onChangeText={(text) => setGeofenceData({ ...geofenceData, address: text })}
                placeholder="Full address"
                multiline
                numberOfLines={3}
                placeholderTextColor="#9CA3AF"
              />

              <TouchableOpacity
                style={styles.submitButton}
                onPress={handleCreateGeofence}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.submitButtonText}>Create Geofence</Text>
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
  statsGrid: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4F46E5',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 4,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 32,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
  },
  emptyText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 12,
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
  leaveName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  leaveTypeBadge: {
    backgroundColor: '#E0E7FF',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  leaveTypeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4F46E5',
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
    marginBottom: 16,
  },
  leaveActions: {
    flexDirection: 'row',
    gap: 8,
  },
  approveButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#10B981',
    paddingVertical: 12,
    borderRadius: 8,
  },
  rejectButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EF4444',
    paddingVertical: 12,
    borderRadius: 8,
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  attendanceCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  attendanceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  attendanceName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
  },
  attendanceTime: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  attendanceTimeText: {
    fontSize: 14,
    color: '#6B7280',
    marginLeft: 6,
  },
  userCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  userAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#E0E7FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userDetails: {
    marginLeft: 12,
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  userEmail: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  userRole: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
    textTransform: 'capitalize',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  noAccessContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
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