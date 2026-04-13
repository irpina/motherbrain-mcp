"use client";

import { useEffect, useRef, useState } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { api } from "@/lib/api";
import { X, Terminal as TerminalIcon, Loader2 } from "lucide-react";
import "@xterm/xterm/css/xterm.css";

interface AgentTerminalModalProps {
  isOpen: boolean;
  onClose: () => void;
  agentId: string;
  agentType: string;
  containerId: string;
}

export function AgentTerminalModal({
  isOpen,
  onClose,
  agentId,
  agentType,
  containerId,
}: AgentTerminalModalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalInstanceRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !terminalRef.current) return;

    let isCleanedUp = false;

    const initTerminal = async () => {
      setIsConnecting(true);
      setError(null);

      try {
        // Get terminal token
        const tokenData = await api.createTerminalToken(agentId);
        const { token } = tokenData;

        // Initialize xterm.js
        const terminal = new Terminal({
          cursorBlink: true,
          fontSize: 14,
          fontFamily: 'Menlo, Monaco, "Courier New", monospace',
          theme: {
            background: "#1e1e1e",
            foreground: "#d4d4d4",
            cursor: "#d4d4d4",
            selectionBackground: "#264f78",
            black: "#000000",
            red: "#cd3131",
            green: "#0dbc79",
            yellow: "#e5e510",
            blue: "#2472c8",
            magenta: "#bc3fbc",
            cyan: "#11a8cd",
            white: "#e5e5e5",
          },
        });

        const fitAddon = new FitAddon();
        terminal.loadAddon(fitAddon);

        terminalInstanceRef.current = terminal;
        fitAddonRef.current = fitAddon;

        // Open terminal in container
        terminal.open(terminalRef.current);
        fitAddon.fit();

        // Connect WebSocket
        const wsUrl = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api-proxy/agents/spawned/${agentId}/terminal-ws?token=${token}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnecting(false);
          terminal.writeln("\r\n\x1b[32mConnected to agent container\x1b[0m\r\n");
        };

        ws.onmessage = (event) => {
          terminal.write(event.data);
        };

        ws.onerror = (err) => {
          setIsConnecting(false);
          setError("WebSocket error occurred");
          terminal.writeln("\r\n\x1b[31mConnection error\x1b[0m\r\n");
        };

        ws.onclose = () => {
          setIsConnecting(false);
          terminal.writeln("\r\n\x1b[33mConnection closed\x1b[0m\r\n");
        };

        // Forward terminal input to WebSocket
        terminal.onData((data) => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(data);
          }
        });

        // Handle resize
        const handleResize = () => {
          fitAddon.fit();
        };
        window.addEventListener("resize", handleResize);

        return () => {
          window.removeEventListener("resize", handleResize);
        };
      } catch (err: unknown) {
        setIsConnecting(false);
        setError(err instanceof Error ? err.message : "Failed to connect");
      }
    };

    const cleanupPromise = initTerminal();

    return () => {
      isCleanedUp = true;
      wsRef.current?.close();
      terminalInstanceRef.current?.dispose();
      terminalInstanceRef.current = null;
      fitAddonRef.current = null;
      wsRef.current = null;
    };
  }, [isOpen, agentId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#1e1e1e] rounded-lg shadow-lg w-[90vw] h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
          <div className="flex items-center gap-2 text-white">
            <TerminalIcon size={18} />
            <span className="font-medium">
              {agentType} - {containerId}
            </span>
            {isConnecting && (
              <Loader2 size={16} className="animate-spin text-slate-400" />
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
          >
            <X size={18} />
          </button>
        </div>

        {/* Terminal */}
        <div className="flex-1 p-2 overflow-hidden">
          {error ? (
            <div className="h-full flex items-center justify-center text-red-400">
              Error: {error}
            </div>
          ) : (
            <div ref={terminalRef} className="h-full w-full" />
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-slate-700 text-xs text-slate-400">
          Press Ctrl+C to send interrupt • Type &apos;exit&apos; to close shell
        </div>
      </div>
    </div>
  );
}
