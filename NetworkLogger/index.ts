import { NetworkLoggerConfig, NetworkLogEntry } from './types';
import { NetworkLogStorage } from './storage';
import { NetworkMonitor } from './monitor';
import { NetworkLogUploader } from './uploader';

/**
 * Main NetworkLogger class that orchestrates all components
 */
export class NetworkLogger {
  private config: Required<NetworkLoggerConfig>;
  private storage: NetworkLogStorage;
  private monitor: NetworkMonitor;
  private uploader: NetworkLogUploader;

  constructor(config: NetworkLoggerConfig) {
    this.config = {
      storageKey: config.storageKey || 'network_logs',
      maxLogs: config.maxLogs || 100,
      enableConsoleLogging: config.enableConsoleLogging ?? true,
      onLogEntry: config.onLogEntry || (() => {}),
      serverUrl: config.serverUrl || '',
      uploadEndpoint: config.uploadEndpoint || '/api/logs/network',
      sessionContextProvider: config.sessionContextProvider
    };

    // Initialize components
    this.storage = new NetworkLogStorage(
      this.config.storageKey,
      this.config.maxLogs,
      this.config.enableConsoleLogging
    );

    this.monitor = new NetworkMonitor(
      this.config.enableConsoleLogging,
      this.handleLogEntry.bind(this)
    );

    this.uploader = new NetworkLogUploader(
      this.config.serverUrl,
      this.config.uploadEndpoint,
      this.storage,
      this.config.enableConsoleLogging
    );
  }

  /**
   * Start monitoring network changes
   */
  async start(): Promise<void> {
    await this.monitor.start();
  }

  /**
   * Stop monitoring network changes
   */
  stop(): void {
    this.monitor.stop();
  }

  /**
   * Update server connection status and log changes
   */
  async setServerConnectionStatus(connected: boolean): Promise<void> {
    await this.monitor.setServerConnectionStatus(connected);
  }

  /**
   * Get current server connection status
   */
  getServerConnectionStatus(): boolean {
    return this.monitor.getServerConnectionStatus();
  }

  /**
   * Get all stored logs
   */
  async getLogs(): Promise<NetworkLogEntry[]> {
    return this.storage.getLogs();
  }

  /**
   * Clear all stored logs
   */
  async clearLogs(): Promise<void> {
    return this.storage.clearLogs();
  }

  /**
   * Get logs since a specific timestamp
   */
  async getLogsSince(timestamp: string): Promise<NetworkLogEntry[]> {
    return this.storage.getLogsSince(timestamp);
  }

  /**
   * Get total number of stored logs
   */
  async getLogsCount(): Promise<number> {
    return this.storage.getLogsCount();
  }

  /**
   * Get logs within a date range
   */
  async getLogsInRange(startDate: string, endDate: string): Promise<NetworkLogEntry[]> {
    return this.storage.getLogsInRange(startDate, endDate);
  }

  /**
   * Upload logs to server and clear local storage on success
   */
  async uploadLogs(): Promise<boolean> {
    return this.uploader.uploadLogs();
  }

  /**
   * Upload specific logs without clearing storage
   */
  async uploadSpecificLogs(logs: NetworkLogEntry[]): Promise<boolean> {
    return this.uploader.uploadSpecificLogs(logs);
  }

  /**
   * Update server configuration
   */
  updateServerConfig(serverUrl: string, uploadEndpoint?: string): void {
    this.uploader.updateServerConfig(serverUrl, uploadEndpoint);
  }

  /**
   * Manually log a custom event
   */
  async logCustomEvent(eventType: string, additionalInfo?: string): Promise<void> {
    this.monitor.logCustomEvent(eventType, additionalInfo);
  }

  /**
   * Handle new log entries from monitor
   */
  private async handleLogEntry(entry: NetworkLogEntry): Promise<void> {
    // Populate session context if provider is configured
    if (this.config.sessionContextProvider) {
      try {
        entry.sessionContext = await this.config.sessionContextProvider();
      } catch (error) {
        if (this.config.enableConsoleLogging) {
          console.warn('[NetworkLogger] Failed to get session context:', error);
        }
      }
    }
    
    // Save to storage
    await this.storage.saveLogEntry(entry);
    
    // Trigger custom callback
    this.config.onLogEntry(entry);
  }
}

// Export types for external use
export * from './types';
export { NetworkLogStorage } from './storage';
export { NetworkMonitor } from './monitor';
export { NetworkLogUploader } from './uploader';