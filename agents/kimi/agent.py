#!/usr/bin/env python3
"""
Motherbrain Kimi Agent (Moonshot AI)

A containerized Moonshot Kimi agent that connects to Motherbrain via MCP
and participates in chat channels.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from openai import OpenAI


class MotherbrainAgent:
    def __init__(self):
        self.api_key = os.getenv("MOONSHOT_API_KEY")
        self.mcp_server = os.getenv("MCP_SERVER_URL", "http://api:8000/mcp")
        self.mcp_api_key = os.getenv("MCP_API_KEY", "supersecret")
        self.channel = os.getenv("CHANNEL", "general")
        self.task = os.getenv("TASK", "")
        self.name = os.getenv("AGENT_NAME", "kimi")
        self.model = os.getenv("KIMI_MODEL", "moonshot-v1-8k")
        
        if not self.api_key:
            print("ERROR: MOONSHOT_API_KEY not set")
            sys.exit(1)
        
        # Moonshot uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.cursor = 0
        self.message_history = []
        
    async def call_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool on the Motherbrain server using httpx with proper handshake."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Step 1: Initialize handshake
            init_payload = {
                "jsonrpc": "2.0",
                "id": "init-1",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": self.name, "version": "1.0"}
                }
            }
            
            init_resp = await client.post(
                self.mcp_server,
                json=init_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.mcp_api_key,
                    "Accept": "application/json, text/event-stream"
                },
                timeout=10.0
            )
            
            session_id = init_resp.headers.get("mcp-session-id")
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.mcp_api_key,
                "Accept": "application/json, text/event-stream"
            }
            if session_id:
                headers["mcp-session-id"] = session_id
            
            # Step 2: Send initialized notification
            await client.post(
                self.mcp_server,
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                headers=headers,
                timeout=5.0
            )
            
            # Step 3: Call the tool
            tool_payload = {
                "jsonrpc": "2.0",
                "id": "tool-1",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await client.post(
                self.mcp_server,
                json=tool_payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"MCP error: {response.status_code} - {response.text}")
                return {}
            
            # Parse response (might be SSE or JSON)
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                for line in response.text.splitlines():
                    if line.startswith("data:"):
                        data = json.loads(line[5:].strip())
                        return data.get("result", {})
            else:
                data = response.json()
                return data.get("result", {})
            
            return {}
    
    async def join_channel(self):
        """Announce presence in the channel."""
        print(f"Joining channel: {self.channel}")
        result = await self.call_mcp_tool("chat_join", {
            "sender": self.name,
            "channel": self.channel
        })
        print(f"Join result: {result}")
    
    async def send_message(self, text: str):
        """Send a message to the channel."""
        result = await self.call_mcp_tool("chat_send", {
            "sender": self.name,
            "message": text,
            "channel": self.channel
        })
        return result
    
    async def read_messages(self) -> list:
        """Read new messages from the channel."""
        result = await self.call_mcp_tool("chat_read", {
            "sender": self.name,
            "channel": self.channel,
            "since_id": self.cursor,
            "limit": 50
        })
        
        messages = result.get("messages", [])
        new_cursor = result.get("cursor", self.cursor)
        
        if new_cursor > self.cursor:
            self.cursor = new_cursor
        
        return messages
    
    def should_respond(self, message: dict) -> bool:
        """Determine if we should respond to a message."""
        sender = message.get("sender", "")
        text = message.get("text", "")
        
        # Don't respond to ourselves
        if sender == self.name:
            return False
        
        # Don't respond to system messages
        if message.get("type") in ["system", "join"]:
            return False
        
        # Respond if mentioned by name
        if f"@{self.name}" in text.lower():
            return True
        
        # Respond if mentioned with @agent or @kimi
        if "@agent" in text.lower() or "@kimi" in text.lower():
            return True
        
        # Don't respond to other messages (avoid spam)
        return False
    
    async def generate_response(self, messages: list) -> str:
        """Generate a response using Moonshot Kimi."""
        # Build conversation context
        system_msg = "You are Kimi, an AI assistant participating in a chat channel. "
        system_msg += "Be helpful, concise, and friendly. Keep responses brief (1-3 sentences)."
        
        # Build messages for Moonshot (OpenAI-compatible)
        openai_messages = [{"role": "system", "content": system_msg}]
        
        # Add recent conversation history
        for msg in messages[-10:]:
            sender = msg.get("sender", "unknown")
            text = msg.get("text", "")
            
            if sender == self.name:
                openai_messages.append({"role": "assistant", "content": text})
            else:
                openai_messages.append({"role": "user", "content": f"{sender}: {text}"})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                messages=openai_messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm having trouble processing that. Could you rephrase?"
    
    async def run(self):
        """Main agent loop."""
        print(f"=== Motherbrain Kimi Agent ===")
        print(f"Server: {self.mcp_server}")
        print(f"Channel: {self.channel}")
        print(f"Name: {self.name}")
        print(f"Model: {self.model}")
        print("")
        
        # Join channel
        await self.join_channel()
        
        # Announce task if provided
        if self.task:
            await self.send_message(f"Starting task: {self.task}")
        
        print("Entering chat loop...")
        print("Press Ctrl+C to exit")
        print("")
        
        # Main loop
        while True:
            try:
                # Read new messages
                messages = await self.read_messages()
                
                # Process messages that need responses
                for msg in messages:
                    if self.should_respond(msg):
                        sender = msg.get("sender", "unknown")
                        print(f"Responding to {sender}...")
                        
                        # Generate and send response
                        response = await self.generate_response(messages)
                        await self.send_message(response)
                        print(f"Sent: {response[:100]}...")
                
                # Sleep before next poll
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                await asyncio.sleep(10)


if __name__ == "__main__":
    agent = MotherbrainAgent()
    asyncio.run(agent.run())
