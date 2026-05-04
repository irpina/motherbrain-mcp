"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { Plus, Send, Users, MessageSquare, Lock, Briefcase } from "lucide-react";

interface Channel {
  id: string;
  name: string;
  private: boolean;
  created_at: string;
}

interface ChatMessage {
  id: number;
  sender: string;
  text: string;
  type: string;
  reply_to: number | null;
  created_at: string;
}

export default function ChatPage() {
  const queryClient = useQueryClient();
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null);
  const [newChannelName, setNewChannelName] = useState("");
  const [showNewChannel, setShowNewChannel] = useState(false);
  const [showJobsPanel, setShowJobsPanel] = useState(false);
  const [messageInput, setMessageInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch jobs
  const { data: jobsData } = useQuery({
    queryKey: ["chat", "jobs"],
    queryFn: () => api.listChatJobs({ status: "open", limit: 50 }),
    refetchInterval: 30000,
    enabled: showJobsPanel,
  });

  // Fetch channels
  const { data: channels, isLoading: channelsLoading } = useQuery({
    queryKey: ["chat", "channels"],
    queryFn: () => api.listChannels(),
    refetchInterval: 30000,
  });

  // Create channel
  const handleCreateChannel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newChannelName.trim()) return;
    try {
      await api.createChannel(newChannelName.trim());
      setNewChannelName("");
      setShowNewChannel(false);
      queryClient.invalidateQueries({ queryKey: ["chat", "channels"] });
    } catch (err: unknown) {
      alert(`Failed to create channel: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Load initial messages when channel selected
  useEffect(() => {
    if (!selectedChannel) {
      setMessages([]);
      return;
    }

    // Load message history
    api.getChannelMessages(selectedChannel).then((data) => {
      setMessages(data.messages || []);
    });
  }, [selectedChannel]);

  // WebSocket connection (token-exchange pattern)
  // Route handlers cannot proxy WS upgrades (fetch() does not handle protocol
  // upgrades). Instead: fetch a short-lived token via the proxy (validates API
  // key server-side), then connect the WebSocket directly to port 8000.
  useEffect(() => {
    if (!selectedChannel) return;

    let ws: WebSocket | null = null;
    let cancelled = false;

    (async () => {
      try {
        const res = await fetch(`/api-proxy/chat/ws-token/`, { method: "POST" });
        if (!res.ok || cancelled) return;
        const { token } = await res.json();

        const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsHost = window.location.hostname;
        const wsUrl = `${wsProto}//${wsHost}:8000/chat/ws/channels/${selectedChannel}?token=${token}`;
        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => { if (!cancelled) setWsConnected(true); };
        ws.onclose = () => { if (!cancelled) setWsConnected(false); };
        ws.onerror = () => { if (!cancelled) setWsConnected(false); };
        ws.onmessage = (event) => {
          if (cancelled) return;
          const msg = JSON.parse(event.data);
          setMessages((prev) => [...prev, msg]);
        };
      } catch {
        if (!cancelled) setWsConnected(false);
      }
    })();

    return () => {
      cancelled = true;
      ws?.close();
    };
  }, [selectedChannel]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Send message
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim() || !selectedChannel) return;

    try {
      await api.postMessage(selectedChannel, "admin", messageInput.trim());
      setMessageInput("");
    } catch (err: unknown) {
      alert(`Failed to send: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Get sender color based on name hash
  const getSenderColor = (name: string) => {
    const colors = [
      "text-blue-600 bg-blue-50",
      "text-green-600 bg-green-50",
      "text-purple-600 bg-purple-50",
      "text-orange-600 bg-orange-50",
      "text-pink-600 bg-pink-50",
      "text-cyan-600 bg-cyan-50",
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  if (channelsLoading) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <div className="w-64 bg-slate-50 border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Channels</h2>
            <button
              onClick={() => setShowNewChannel(true)}
              className="p-1 hover:bg-slate-200 rounded"
            >
              <Plus size={18} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {channels?.map((channel: Channel) => (
            <button
              key={channel.id}
              onClick={() => setSelectedChannel(channel.name)}
              className={`w-full text-left px-4 py-2 hover:bg-slate-100 flex items-center gap-2 ${
                selectedChannel === channel.name ? "bg-slate-200" : ""
              }`}
            >
              {channel.private ? (
                <Lock size={16} className="text-slate-400" />
              ) : (
                <MessageSquare size={16} className="text-slate-400" />
              )}
              <span className="truncate">{channel.name}</span>
              {channel.private && (
                <span className="ml-auto text-[10px] text-slate-400">private</span>
              )}
            </button>
          ))}
          {channels?.length === 0 && (
            <div className="p-4 text-sm text-slate-400">No channels yet</div>
          )}
        </div>

        {showNewChannel && (
          <div className="p-4 border-t bg-white">
            <form onSubmit={handleCreateChannel}>
              <input
                type="text"
                value={newChannelName}
                onChange={(e) => setNewChannelName(e.target.value)}
                placeholder="Channel name"
                className="w-full px-3 py-2 border rounded text-sm mb-2"
                autoFocus
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowNewChannel(false)}
                  className="flex-1 px-3 py-1 text-sm border rounded hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {selectedChannel ? (
          <>
            {/* Header */}
            <div className="px-4 py-3 border-b flex items-center justify-between">
              <div>
                <h3 className="font-semibold">#{selectedChannel}</h3>
                <div className="text-xs text-slate-400 flex items-center gap-2">
                  <span className={wsConnected ? "text-green-500" : "text-red-500"}>
                    ● {wsConnected ? "Connected" : "Disconnected"}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setShowJobsPanel(!showJobsPanel)}
                  className={`p-2 rounded ${showJobsPanel ? "bg-blue-100 text-blue-600" : "hover:bg-slate-100 text-slate-400"}`}
                  title="Jobs"
                >
                  <Briefcase size={18} />
                </button>
                <button className="p-2 hover:bg-slate-100 rounded text-slate-400">
                  <Users size={18} />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((msg) => (
                <div key={msg.id} className="group">
                  {msg.type === "system" || msg.type === "join" ? (
                    <div className="text-center text-xs text-slate-400 py-2">
                      {msg.text}
                    </div>
                  ) : (
                    <div className="flex gap-3">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${getSenderColor(
                          msg.sender
                        )}`}
                      >
                        {msg.sender.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-baseline gap-2">
                          <span className="font-medium text-sm">{msg.sender}</span>
                          <span className="text-xs text-slate-400">
                            {formatRelativeTime(msg.created_at)}
                          </span>
                        </div>
                        <div className="text-sm text-slate-700 mt-0.5">{msg.text}</div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSend} className="p-4 border-t">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={!messageInput.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send size={18} />
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            <div className="text-center">
              <MessageSquare size={48} className="mx-auto mb-4 opacity-50" />
              <p>Select a channel to start chatting</p>
            </div>
          </div>
        )}
      </div>

      {/* Jobs Panel */}
      {showJobsPanel && (
        <div className="w-80 bg-white border-l flex flex-col">
          <div className="p-4 border-b">
            <h2 className="font-semibold flex items-center gap-2">
              <Briefcase size={18} />
              Open Jobs
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {jobsData?.jobs?.length === 0 && (
              <div className="text-sm text-slate-400 text-center py-8">No open jobs</div>
            )}
            {jobsData?.jobs?.map((job: any) => (
              <div key={job.id} className="border rounded-lg p-3 hover:bg-slate-50">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-medium text-sm">{job.title}</h4>
                  <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 rounded text-slate-500 uppercase">
                    {job.category}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1 line-clamp-3">{job.body}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-[10px] text-slate-400">#{job.channel}</span>
                  <button
                    onClick={async () => {
                      try {
                        await api.claimChatJob(job.id);
                        queryClient.invalidateQueries({ queryKey: ["chat", "jobs"] });
                        queryClient.invalidateQueries({ queryKey: ["chat", "channels"] });
                        alert(`Claimed job: ${job.title}`);
                      } catch (err: unknown) {
                        alert(`Failed to claim: ${err instanceof Error ? err.message : String(err)}`);
                      }
                    }}
                    className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Claim
                  </button>
                </div>
              </div>
            ))}
            {!jobsData && (
              <div className="text-sm text-slate-400 text-center py-8">Loading jobs...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
