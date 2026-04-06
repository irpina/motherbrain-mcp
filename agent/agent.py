#!/usr/bin/env python3
"""
Example Motherbrain Agent

This is a sample agent that:
1. Registers with the Motherbrain API (or uses existing token)
2. Sends heartbeats every 10 seconds
3. Polls /jobs/next for work
4. Executes jobs and reports status
5. Receives and sends messages to other agents
"""

import os
import json
import time
import threading
from typing import Optional
import requests


API_URL = os.getenv("API_URL", "http://localhost:8000")
MASTER_API_KEY = os.getenv("MASTER_API_KEY", "supersecret")  # For initial registration
AGENT_TOKEN = os.getenv("AGENT_TOKEN")  # If already registered
PLATFORM = os.getenv("PLATFORM", "python-agent")
CAPABILITIES = json.loads(os.getenv("CAPABILITIES", '["python", "shell"]'))


class MotherbrainAgent:
    def __init__(self):
        self.agent_id: Optional[str] = None
        self.agent_token: Optional[str] = AGENT_TOKEN
        self.headers: dict = {}
        self.running = False
        self._update_headers()
        
    def _update_headers(self):
        """Update headers with current token."""
        if self.agent_token:
            self.headers = {"X-Agent-Token": self.agent_token}
        else:
            self.headers = {"X-API-Key": MASTER_API_KEY}
    
    def register(self) -> bool:
        """Register the agent with the Motherbrain API."""
        if self.agent_token:
            print(f"🔑 Using existing agent token")
            # Verify the token works
            try:
                response = requests.get(
                    f"{API_URL}/messages/inbox?limit=1",
                    headers=self.headers
                )
                if response.status_code != 403:
                    print("✅ Token verified")
                    return True
            except Exception as e:
                print(f"⚠️ Token verification failed: {e}")
                return False
        
        # Register new agent
        payload = {
            "platform": PLATFORM,
            "capabilities": {cap: True for cap in CAPABILITIES}
        }
        try:
            response = requests.post(
                f"{API_URL}/agents/register",
                json=payload,
                headers={"X-API-Key": MASTER_API_KEY}
            )
            response.raise_for_status()
            data = response.json()
            self.agent_id = data["agent_id"]
            self.agent_token = data["token"]
            self._update_headers()
            print(f"✅ Registered agent: {self.agent_id}")
            print(f"🔑 Token: {self.agent_token}")
            print("⚠️  Save this token as AGENT_TOKEN env var for future runs!")
            return True
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            return False
    
    def send_heartbeat(self):
        """Send a heartbeat to keep the agent online."""
        if not self.agent_token:
            return
        try:
            response = requests.post(
                f"{API_URL}/agents/heartbeat",
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"💓 Heartbeat sent")
        except Exception as e:
            print(f"⚠️ Heartbeat failed: {e}")
    
    def heartbeat_loop(self):
        """Background thread for heartbeats."""
        while self.running:
            self.send_heartbeat()
            time.sleep(10)
    
    def get_next_job(self) -> Optional[dict]:
        """Poll for the next available job."""
        if not self.agent_token:
            return None
        try:
            response = requests.get(
                f"{API_URL}/jobs/next",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 204:
                return None
        except Exception as e:
            print(f"⚠️ Job poll failed: {e}")
        return None
    
    def update_job_status(self, job_id: str, status: str, log: Optional[str] = None):
        """Update the status of a job."""
        payload = {"status": status}
        if log:
            payload["log"] = log
        try:
            response = requests.post(
                f"{API_URL}/jobs/{job_id}/status",
                json=payload,
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"📝 Job {job_id} status updated to: {status}")
        except Exception as e:
            print(f"⚠️ Status update failed: {e}")
    
    def execute_job(self, job: dict):
        """Execute a job (mock implementation)."""
        job_id = job["job_id"]
        job_type = job["type"]
        payload = job.get("payload", {})
        
        print(f"🚀 Executing job {job_id} (type: {job_type})")
        
        # Update status to running
        self.update_job_status(job_id, "running")
        
        # Mock execution
        time.sleep(2)
        
        # Simulate work based on job type
        if job_type == "echo":
            result = f"Echo: {payload.get('message', 'Hello')}" if payload else "Echo: Hello"
        elif job_type == "sleep":
            duration = payload.get("duration", 1) if payload else 1
            time.sleep(duration)
            result = f"Slept for {duration} seconds"
        elif job_type == "shell":
            import subprocess
            cmd = payload.get("command", "echo 'Hello World'") if payload else "echo 'Hello World'"
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result = result.stdout.strip() or result.stderr.strip() or "Command executed"
            except Exception as e:
                result = f"Command failed: {e}"
        else:
            result = f"Completed job of type: {job_type}"
        
        print(f"✅ Job {job_id} completed: {result}")
        
        # Update status to completed
        self.update_job_status(job_id, "completed", log=result)
    
    def check_messages(self):
        """Check for new messages in inbox."""
        if not self.agent_token:
            return
        try:
            response = requests.get(
                f"{API_URL}/messages/inbox?unread_only=true",
                headers=self.headers
            )
            if response.status_code == 200:
                messages = response.json()
                for msg in messages:
                    print(f"📨 Message from {msg['sender_id']}: {msg['content']}")
        except Exception as e:
            print(f"⚠️ Message check failed: {e}")
    
    def run(self):
        """Main agent loop."""
        # Register or verify
        if not self.register():
            print("Failed to register/verify, exiting.")
            return
        
        self.running = True
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        print(f"🤖 Agent is running...")
        print(f"   API: {API_URL}")
        print(f"   Token: {self.agent_token[:16]}...")
        
        # Main work loop
        try:
            while self.running:
                # Check for messages
                self.check_messages()
                
                # Get next job
                job = self.get_next_job()
                if job:
                    self.execute_job(job)
                else:
                    print("⏳ No jobs available, waiting...")
                    time.sleep(5)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down agent...")
            self.running = False


if __name__ == "__main__":
    agent = MotherbrainAgent()
    agent.run()
