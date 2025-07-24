import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { NetworkEventType, NetworkLogEntry, NetworkLoggerState } from './types';

/**
 * Network monitoring and event detection
 */
export class NetworkMonitor {
  private state: NetworkLoggerState;
  private enableConsoleLogging: boolean;
  private onLogEntry: (entry: NetworkLogEntry) => void;

  constructor(enableConsoleLogging: boolean, onLogEntry: (entry: NetworkLogEntry) => void) {
    this.enableConsoleLogging = enableConsoleLogging;
    this.onLogEntry = onLogEntry;
    this.state = {
      previousSubnet: null,
      previousNetworkState: null,
      serverConnected: false,
      unsubscribeNetInfo: null
    };
  }

  /**
   * Start monitoring network changes
   */
  async start(): Promise<void> {
    try {
      // Set initial network state
      const initialState = await NetInfo.fetch();
      await this.handleNetworkStateChange(initialState);

      // Subscribe to network changes
      this.state.unsubscribeNetInfo = NetInfo.addEventListener(
        this.handleNetworkStateChange.bind(this)
      );
      
      if (this.enableConsoleLogging) {
        console.log('[NetworkMonitor] Started monitoring network changes');
      }
    } catch (error) {
      console.error('[NetworkMonitor] Failed to start monitoring:', error);
    }
  }

  /**
   * Stop monitoring network changes
   */
  stop(): void {
    if (this.state.unsubscribeNetInfo) {
      this.state.unsubscribeNetInfo();
      this.state.unsubscribeNetInfo = null;
    }
    
    if (this.enableConsoleLogging) {
      console.log('[NetworkMonitor] Stopped monitoring network changes');
    }
  }

  /**
   * Update server connection status
   */
  async setServerConnectionStatus(connected: boolean): Promise<void> {
    if (this.state.serverConnected !== connected) {
      this.state.serverConnected = connected;
      
      try {
        const currentNetworkState = await NetInfo.fetch();

        const eventType = connected ? 'server_connection_restored' : 'server_connection_lost';

        const entry = this.createLogEntry(eventType, currentNetworkState, this.state.serverConnected);

        this.onLogEntry(entry);

      } catch (error) {
        console.error('[NetworkMonitor] Failed to fetch current network state:', error);
      }
    }
  }

  /**
   * Get current server connection status
   */
  getServerConnectionStatus(): boolean {
    return this.state.serverConnected;
  }

  /**
   * Manually create a custom log entry
   */
  logCustomEvent(eventType: string, additionalInfo?: string): void {
    if (this.state.previousNetworkState) {
      const entry = this.createLogEntry(eventType as any, this.state.previousNetworkState, this.state.serverConnected, additionalInfo);
      this.onLogEntry(entry);
    }
  }

  /**
   * Handle network state changes and log relevant events
   */
  private async handleNetworkStateChange(state: NetInfoState): Promise<void> {
    await this.checkForSubnetChange(state);
    await this.checkForConnectionChange(state);
    
    // Update state for next comparison
    this.state.previousNetworkState = state;
  }

  /**
   * Check if device moved to a different subnet
   */
  private async checkForSubnetChange(state: NetInfoState): Promise<void> {
    if (!state.details || !('ipAddress' in state.details) || typeof state.details.ipAddress !== 'string') return

    const currentSubnet = this.getSubnet(state.details.ipAddress);
    
    if (currentSubnet && this.state.previousSubnet && this.state.previousSubnet !== currentSubnet) {
      const entry = this.createLogEntry('subnet_change', state, this.state.serverConnected, `Previous: ${this.state.previousSubnet}, New: ${currentSubnet}`);
      entry.previousSubnet = this.state.previousSubnet;
      this.onLogEntry(entry);
    }
    
    this.state.previousSubnet = currentSubnet;
  }
  
  /**
   * Check for connection status or type changes
   */
  private async checkForConnectionChange(state: NetInfoState): Promise<void> {
    if (!this.state.previousNetworkState) {
      // First network state - log initial state
      const entry = this.createLogEntry('connection_change', state, this.state.serverConnected, 'Initial network state');
      this.onLogEntry(entry);
      return;
    }

    const wasConnected = this.state.previousNetworkState.isConnected;
    const isConnected = state.isConnected;
    
    // Check for connect/disconnect events
    if (wasConnected !== isConnected) {
      const eventType = isConnected ? 'reconnect' : 'disconnect';
      const entry = this.createLogEntry(eventType, state, this.state.serverConnected);
      this.onLogEntry(entry);
    }
    // Check for other connection changes (type, reachability)
    else if (this.state.previousNetworkState.type !== state.type || this.state.previousNetworkState.isInternetReachable !== state.isInternetReachable) {
      const entry = this.createLogEntry('connection_change', state, this.state.serverConnected);
      this.onLogEntry(entry);
    }
  }

  /**
   * Create a log entry from current network state
   */
  private createLogEntry(eventType: NetworkEventType, state: NetInfoState, serverConnected: boolean, additionalInfo?: string): NetworkLogEntry {
    const entry: NetworkLogEntry = {
      timestamp: new Date().toISOString(),
      eventType,
      networkType: state.type,
      isConnected: state.isConnected,
      isInternetReachable: state.isInternetReachable,
      serverConnected,
      additionalInfo,
      details: state.details
    };

    // Extract IP and subnet information
    if (state.details && 'ipAddress' in state.details && typeof state.details.ipAddress === 'string') {
      entry.ipAddress = state.details.ipAddress;
      entry.subnet = this.getSubnet(state.details.ipAddress) || undefined;
    }

    // Extract WiFi specific information
    if (state.type === 'wifi' && state.details) {
      const wifiDetails = state.details as any;
      entry.ssid = wifiDetails.ssid || 'unknown';
      entry.bssid = wifiDetails.bssid || 'unknown';
    }

    // Extract cellular specific information
    if (state.type === 'cellular' && state.details) {
      const cellularDetails = state.details as any;
      entry.cellularGeneration = cellularDetails.cellularGeneration;
    }

    return entry;
  }

  /**
   * Extract subnet from IP address (first 3 octets)
   */
  private getSubnet(ipAddress: string): string | null {
    if (!ipAddress) return null;
    
    const parts = ipAddress.split('.');
    if (parts.length === 4) {
      return `${parts[0]}.${parts[1]}.${parts[2]}`;
    }
    return null;
  }
}


