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

export default function PayrollScreen() {
  const { user, token } = useAuth();
  const [payrollRecords, setPayrollRecords] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.role === 'super_admin' || user?.role === 'hr_manager';

  useEffect(() => {
    fetchPayroll();
  }, []);

  const fetchPayroll = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/payroll/my-payroll`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPayrollRecords(response.data);
    } catch (error: any) {
      console.error('Error fetching payroll:', error);
      if (error.response?.status === 404) {
        // No payroll records yet
        setPayrollRecords([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchPayroll();
    setRefreshing(false);
  };

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN')}`;
  };

  const handleGeneratePayroll = async () => {
    Alert.alert(
      'Generate Payroll',
      'Generate payroll for current month?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Generate',
          onPress: async () => {
            try {
              const currentMonth = new Date().toISOString().slice(0, 7);
              await axios.post(
                `${API_URL}/api/payroll/generate`,
                { month: currentMonth },
                { headers: { Authorization: `Bearer ${token}` } }
              );
              Alert.alert('Success', 'Payroll generated successfully!');
              fetchPayroll();
            } catch (error: any) {
              Alert.alert('Error', error.response?.data?.detail || 'Failed to generate payroll');
            }
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Payroll Management</Text>
        <Text style={styles.subtitle}>Your salary slips and payments</Text>
      </View>

      {isAdmin && (
        <TouchableOpacity style={styles.generateButton} onPress={handleGeneratePayroll}>
          <Ionicons name="calculator" size={24} color="#FFFFFF" />
          <Text style={styles.generateButtonText}>Generate Payroll</Text>
        </TouchableOpacity>
      )}

      <ScrollView
        style={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {loading ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>Loading...</Text>
          </View>
        ) : payrollRecords.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="document-text-outline" size={64} color="#9CA3AF" />
            <Text style={styles.emptyText}>No payroll records yet</Text>
            <Text style={styles.emptySubtext}>
              {isAdmin ? 'Generate payroll for the month' : 'Payroll will appear here once generated'}
            </Text>
          </View>
        ) : (
          payrollRecords.map((record) => (
            <View key={record.id} style={styles.payrollCard}>
              <View style={styles.payrollHeader}>
                <View>
                  <Text style={styles.payrollMonth}>{record.month}</Text>
                  <Text style={styles.payrollEmployee}>{record.employee_name || user?.full_name}</Text>
                </View>
                <View
                  style={[
                    styles.statusBadge,
                    {
                      backgroundColor:
                        record.status === 'finalized'
                          ? '#D1FAE5'
                          : record.status === 'paid'
                          ? '#DBEAFE'
                          : '#FEF3C7',
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.statusText,
                      {
                        color:
                          record.status === 'finalized'
                            ? '#10B981'
                            : record.status === 'paid'
                            ? '#3B82F6'
                            : '#F59E0B',
                      },
                    ]}
                  >
                    {record.status}
                  </Text>
                </View>
              </View>

              <View style={styles.payrollDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Working Days:</Text>
                  <Text style={styles.detailValue}>{record.working_days}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Present Days:</Text>
                  <Text style={styles.detailValue}>{record.present_days}</Text>
                </View>
                {record.lwp_days > 0 && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>LWP Days:</Text>
                    <Text style={[styles.detailValue, styles.negativeValue]}>-{record.lwp_days}</Text>
                  </View>
                )}
              </View>

              <View style={styles.divider} />

              <View style={styles.salarySection}>
                <View style={styles.salaryRow}>
                  <Text style={styles.salaryLabel}>Base Salary:</Text>
                  <Text style={styles.salaryValue}>{formatCurrency(record.base_salary)}</Text>
                </View>

                {record.unused_cl_encashment > 0 && (
                  <View style={styles.salaryRow}>
                    <Text style={styles.salaryLabel}>CL Encashment:</Text>
                    <Text style={[styles.salaryValue, styles.positiveValue]}>
                      +{formatCurrency(record.unused_cl_encashment)}
                    </Text>
                  </View>
                )}

                {record.compensatory_payment > 0 && (
                  <View style={styles.salaryRow}>
                    <Text style={styles.salaryLabel}>Compensatory:</Text>
                    <Text style={[styles.salaryValue, styles.positiveValue]}>
                      +{formatCurrency(record.compensatory_payment)}
                    </Text>
                  </View>
                )}

                <View style={styles.salaryRow}>
                  <Text style={styles.salaryLabel}>Gross Salary:</Text>
                  <Text style={styles.salaryValue}>{formatCurrency(record.gross_salary)}</Text>
                </View>

                {Object.keys(record.deductions || {}).length > 0 && (
                  <View style={styles.deductionsSection}>
                    <Text style={styles.deductionsTitle}>Deductions:</Text>
                    {Object.entries(record.deductions).map(([key, value]: [string, any]) => (
                      <View key={key} style={styles.salaryRow}>
                        <Text style={styles.deductionLabel}>  - {key.toUpperCase()}:</Text>
                        <Text style={[styles.salaryValue, styles.negativeValue]}>
                          -{formatCurrency(value)}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>

              <View style={styles.divider} />

              <View style={styles.netSalaryRow}>
                <Text style={styles.netSalaryLabel}>Net Salary:</Text>
                <Text style={styles.netSalaryValue}>{formatCurrency(record.net_salary)}</Text>
              </View>

              <View style={styles.cardFooter}>
                <Text style={styles.footerText}>
                  Generated: {new Date(record.generated_at).toLocaleDateString()}
                </Text>
                <TouchableOpacity style={styles.downloadButton}>
                  <Ionicons name="download-outline" size={16} color="#1E3A8A" />
                  <Text style={styles.downloadText}>Download</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </ScrollView>
    </View>
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
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#10B981',
    marginHorizontal: 16,
    marginVertical: 16,
    paddingVertical: 16,
    borderRadius: 12,
  },
  generateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#6B7280',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 8,
    textAlign: 'center',
  },
  payrollCard: {
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
  payrollHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  payrollMonth: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  payrollEmployee: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  payrollDetails: {
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  negativeValue: {
    color: '#EF4444',
  },
  positiveValue: {
    color: '#10B981',
  },
  divider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 12,
  },
  salarySection: {
    marginBottom: 12,
  },
  salaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  salaryLabel: {
    fontSize: 14,
    color: '#374151',
  },
  salaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  deductionsSection: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  deductionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  deductionLabel: {
    fontSize: 13,
    color: '#6B7280',
  },
  netSalaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    backgroundColor: '#F0F9FF',
    borderRadius: 8,
    paddingHorizontal: 12,
  },
  netSalaryLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1E3A8A',
  },
  netSalaryValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1E3A8A',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
  },
  footerText: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  downloadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#EFF6FF',
  },
  downloadText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1E3A8A',
    marginLeft: 4,
  },
});