import { NetInfoState } from '@react-native-community/netinfo';

// Network event types
export type NetworkEventType = 
  | 'connection_change' 
  | 'subnet_change' 
  | 'disconnect' 
  | 'reconnect' 
  | 'server_connection_lost' 
  | 'server_connection_restored';

export interface SessionContext {
  userId: string | number;
  sessionId?: string;
  deviceId?: string;
  handsetId?: string | number;
  serviceLocationId?: string | number;
  responseAreaIds?: (string | number)[];
  userRole?: string;
  [key: string]: any; // Allow any additional context
}

// Context provider function type
export type SessionContextProvider = () => Promise<SessionContext> | SessionContext;

// Log entry structure
export interface NetworkLogEntry {
  timestamp: string;
  eventType: NetworkEventType;
  networkType: string | null;
  isConnected: boolean | null;
  isInternetReachable: boolean | null;
  serverConnected?: boolean;
  additionalInfo?: string;
  
  // Network details
  ipAddress?: string;
  subnet?: string;
  previousSubnet?: string;
  
  // WiFi specific
  ssid?: string;
  bssid?: string;
  
  // Cellular specific
  cellularGeneration?: string;
  
  // Raw NetInfo details
  details?: any;
  
  // Flexible session context
  sessionContext?: SessionContext;
}

// Configuration interface
export interface NetworkLoggerConfig {
  storageKey?: string;
  maxLogs?: number;
  enableConsoleLogging?: boolean;
  onLogEntry?: (entry: NetworkLogEntry) => void;
  serverUrl?: string;
  uploadEndpoint?: string;
  sessionContextProvider: SessionContextProvider;
}

// Internal state interface
export interface NetworkLoggerState {
  previousSubnet: string | null;
  previousNetworkState: NetInfoState | null;
  serverConnected: boolean;
  unsubscribeNetInfo: (() => void) | null;
}