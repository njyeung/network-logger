import { NetworkLogEntry } from './types';
import { NetworkLogStorage } from './storage';

/**
 * Handles uploading logs to server
 */
export class NetworkLogUploader {
  private serverUrl: string;
  private uploadEndpoint: string;
  private storage: NetworkLogStorage;
  private enableConsoleLogging: boolean;

  constructor(
    serverUrl: string,
    uploadEndpoint: string,
    storage: NetworkLogStorage,
    enableConsoleLogging: boolean
  ) {
    this.serverUrl = serverUrl;
    this.uploadEndpoint = uploadEndpoint;
    this.storage = storage;
    this.enableConsoleLogging = enableConsoleLogging;
  }

  /**
   * Upload logs to server and clear local storage on success
   */
  async uploadLogs(): Promise<boolean> {
    if (!this.serverUrl) {
      console.warn('[NetworkLogUploader] No server URL configured for upload');
      return false;
    }

    try {
      const logs = await this.storage.getLogs();
      if (logs.length === 0) {
        if (this.enableConsoleLogging) {
          console.log('[NetworkLogUploader] No logs to upload');
        }
        return true;
      }

      const success = await this.sendLogsToServer(logs);
      
      if (success) {
        await this.storage.clearLogs();
        if (this.enableConsoleLogging) {
          console.log(`[NetworkLogUploader] Successfully uploaded ${logs.length} logs`);
        }
      }

      return success;
    } catch (error) {
      console.error('[NetworkLogUploader] Upload error:', error);
      return false;
    }
  }

  /**
   * Upload specific logs without clearing storage
   */
  async uploadSpecificLogs(logs: NetworkLogEntry[]): Promise<boolean> {
    if (!this.serverUrl) {
      console.warn('[NetworkLogUploader] No server URL configured for upload');
      return false;
    }

    if (logs.length === 0) {
      if (this.enableConsoleLogging) {
        console.log('[NetworkLogUploader] No logs to upload');
      }
      return true;
    }

    try {
      const success = await this.sendLogsToServer(logs);
      
      if (success && this.enableConsoleLogging) {
        console.log(`[NetworkLogUploader] Successfully uploaded ${logs.length} specific logs`);
      }

      return success;
    } catch (error) {
      console.error('[NetworkLogUploader] Upload error:', error);
      return false;
    }
  }

  /**
   * Send logs to server via HTTP POST
   */
  private async sendLogsToServer(logs: NetworkLogEntry[]): Promise<boolean> {
    const response = await fetch(`${this.serverUrl}${this.uploadEndpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        logs,
        deviceInfo: {
          timestamp: new Date().toISOString(),
          platform: 'mobile'
        }
      })
    });

    if (response.ok) {
      return true;
    } else {
      console.error('[NetworkLogger] Failed to upload logs:', response.status, response.statusText);
      return false;
    }
  }

  /**
   * Update server configuration
   */
  updateServerConfig(serverUrl: string, uploadEndpoint?: string): void {
    this.serverUrl = serverUrl;
    if (uploadEndpoint) {
      this.uploadEndpoint = uploadEndpoint;
    }
  }

  /**
   * Get current server configuration
   */
  getServerConfig(): { serverUrl: string; uploadEndpoint: string } {
    return {
      serverUrl: this.serverUrl,
      uploadEndpoint: this.uploadEndpoint
    };
  }
}