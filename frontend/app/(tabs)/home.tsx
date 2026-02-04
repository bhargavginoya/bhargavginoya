import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function HomeScreen() {
  const { user, token } = useAuth();
  const [todayStatus, setTodayStatus] = useState<any>(null);
  const [leaveBalance, setLeaveBalance] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statusRes, balanceRes] = await Promise.all([
        axios.get(`${API_URL}/api/attendance/today-status`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_URL}/api/leaves/balance`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setTodayStatus(statusRes.data);
      setLeaveBalance(balanceRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hello,</Text>
          <Text style={styles.name}>{user?.full_name}</Text>
          <Text style={styles.role}>{user?.designation || user?.role}</Text>
        </View>
        <View style={styles.avatar}>
          <Ionicons name="person" size={32} color="#FFFFFF" />
        </View>
      </View>

      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons name="time" size={24} color="#4F46E5" />
          <Text style={styles.cardTitle}>Today's Attendance</Text>
        </View>
        {todayStatus?.checked_in ? (
          <View style={styles.statusContainer}>
            <View style={styles.statusRow}>
              <Ionicons name="checkmark-circle" size={20} color="#10B981" />
              <Text style={styles.statusText}>Checked In</Text>
            </View>
            <Text style={styles.timeText}>
              {todayStatus.check_in_time
                ? new Date(todayStatus.check_in_time).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : 'N/A'}
            </Text>
            {todayStatus.checked_out && (
              <View style={[styles.statusRow, styles.mtop]}>
                <Ionicons name="exit" size={20} color="#EF4444" />
                <Text style={styles.statusText}>Checked Out</Text>
                <Text style={styles.timeText}>
                  {new Date(todayStatus.check_out_time).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
              </View>
            )}
          </View>
        ) : (
          <View style={styles.notCheckedIn}>
            <Ionicons name="alert-circle-outline" size={48} color="#F59E0B" />
            <Text style={styles.notCheckedText}>Not checked in yet</Text>
          </View>
        )}
      </View>

      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons name="calendar-outline" size={24} color="#4F46E5" />
          <Text style={styles.cardTitle}>Leave Balance</Text>
        </View>
        <View style={styles.leaveGrid}>
          <View style={styles.leaveItem}>
            <Text style={styles.leaveCount}>{leaveBalance?.sick_balance || 0}</Text>
            <Text style={styles.leaveLabel}>Sick Leave</Text>
          </View>
          <View style={styles.leaveItem}>
            <Text style={styles.leaveCount}>{leaveBalance?.casual_balance || 0}</Text>
            <Text style={styles.leaveLabel}>Casual Leave</Text>
          </View>
          <View style={styles.leaveItem}>
            <Text style={styles.leaveCount}>{leaveBalance?.earned_balance || 0}</Text>
            <Text style={styles.leaveLabel}>Earned Leave</Text>
          </View>
        </View>
      </View>

      <View style={styles.quickActions}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionGrid}>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="finger-print" size={32} color="#4F46E5" />
            <Text style={styles.actionText}>Mark Attendance</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="document-text" size={32} color="#4F46E5" />
            <Text style={styles.actionText}>Apply Leave</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
    paddingTop: 48,
  },
  greeting: {
    fontSize: 16,
    color: '#6B7280',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 4,
  },
  role: {
    fontSize: 14,
    color: '#4F46E5',
    marginTop: 2,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#4F46E5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
  },
  statusContainer: {
    paddingVertical: 8,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    fontSize: 16,
    color: '#374151',
    marginLeft: 8,
    flex: 1,
  },
  timeText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  mtop: {
    marginTop: 12,
  },
  notCheckedIn: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  notCheckedText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 12,
  },
  leaveGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  leaveItem: {
    alignItems: 'center',
    flex: 1,
  },
  leaveCount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4F46E5',
  },
  leaveLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
  quickActions: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  actionGrid: {
    flexDirection: 'row',
    gap: 16,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  actionText: {
    fontSize: 14,
    color: '#374151',
    marginTop: 8,
    textAlign: 'center',
  },
});
