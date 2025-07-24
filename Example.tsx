import React, { useEffect, useRef } from 'react';
import { SafeAreaView, Text } from 'react-native';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { io, Socket } from 'socket.io-client';
import { NetworkLogger, SessionContextProvider } from './NetworkLogger';

export default function App() {
  const networkLogger = useRef<NetworkLogger | null>(null);

  // Helper function to add timestamps to logs
  const logWithTimestamp = (message: string, ...args: any[]): void => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${message}`, ...args);
  };

  useEffect(() => {
    // Initialize NetworkLogger
    networkLogger.current = new NetworkLogger({
      serverUrl: 'http://192.168.2.141:8000',
      uploadEndpoint: '/api/logs/network',
      enableConsoleLogging: true,
      onLogEntry: (entry) => {
        console.log(`[NetworkLogger] New log entry ${entry.eventType}`);
      },
      sessionContextProvider: () => ({
        userId: "unique_user_id",
        sessionId: "session id"
      })
    });

    networkLogger.current.start();

    const socket: Socket = io('http://192.168.2.141:8000', {
      transports: ['websocket'],
    });

    socket.on('connect', async () => {
      await networkLogger.current?.setServerConnectionStatus(true);
      
      if (networkLogger.current) {
        const count = await networkLogger.current.getLogsCount();
        const uploaded = await networkLogger.current.uploadLogs();
      }
    });

    socket.on('disconnect', async () => {
      await networkLogger.current?.setServerConnectionStatus(false);
    });

    socket.on('connect_error', async (err: Error) => {
      await networkLogger.current?.setServerConnectionStatus(false);
    });

    socket.on('message', (msg: any) => {
      console.log(msg)
    });

    return () => {
      socket.disconnect();
      networkLogger.current?.stop();
    };
  }, []);

  return (
    <SafeAreaView>
      <Text>Client</Text>
    </SafeAreaView>
  );
}