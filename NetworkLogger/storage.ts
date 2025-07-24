import AsyncStorage from '@react-native-async-storage/async-storage';
import { NetworkLogEntry } from './types';

/**
 * Storage manager for network logs
 */
export class NetworkLogStorage {
  private storageKey: string;
  private maxLogs: number;
  private enableConsoleLogging: boolean;

  constructor(storageKey: string, maxLogs: number, enableConsoleLogging: boolean) {
    this.storageKey = storageKey;
    this.maxLogs = maxLogs;
    this.enableConsoleLogging = enableConsoleLogging;
  }

  /**
   * Store log entry to AsyncStorage
   */
  async saveLogEntry(entry: NetworkLogEntry): Promise<void> {
    try {
      // Add to storage (newest first)
      const existingLogs = await this.getLogs();
      const newLogs = [entry, ...existingLogs].slice(0, this.maxLogs);
      await AsyncStorage.setItem(this.storageKey, JSON.stringify(newLogs));
      
      if (this.enableConsoleLogging) {
        console.log(`[NetworkLogStorage] ${entry.timestamp} - ${entry.eventType}:`, entry);
      }
    } catch (error) {
      console.error('[NetworkLogStorage] Failed to save log entry:', error);
    }
  }

  /**
   * Get all stored logs
   */
  async getLogs(): Promise<NetworkLogEntry[]> {
    try {
      const logs = await AsyncStorage.getItem(this.storageKey);
      return logs ? JSON.parse(logs) : [];

    } catch (error) {
      console.error('[NetworkLogStorage] Failed to get logs:', error);
      return [];
    }
  }

  /**
   * Clear all stored logs
   */
  async clearLogs(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.storageKey);

      if (this.enableConsoleLogging) {
        console.log('[NetworkLogStorage] Cleared all logs');
      }
    } catch (error) {
      console.error('[NetworkLogStorage] Failed to clear logs:', error);
    }
  }

  /**
   * Get logs created after a specific timestamp
   */
  async getLogsSince(timestamp: string): Promise<NetworkLogEntry[]> {
    const logs = await this.getLogs();
    return logs.filter(log => log.timestamp > timestamp);
  }

  /**
   * Get total number of stored logs
   */
  async getLogsCount(): Promise<number> {
    const logs = await this.getLogs();
    return logs.length;
  }

  /**
   * Get logs within a date range
   */
  async getLogsInRange(startDate: string, endDate: string): Promise<NetworkLogEntry[]> {
    const logs = await this.getLogs();
    return logs.filter(log => log.timestamp >= startDate && log.timestamp <= endDate);
  }
}