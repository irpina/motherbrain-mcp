"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { truncateId } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface User {
  user_id: string;
  name: string;
  email?: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface Group {
  group_id: string;
  name: string;
  description?: string;
  allowed_service_ids: string[];
  created_at: string;
}

export default function UsersAdminPage() {
  const queryClient = useQueryClient();
  const [showNewUserForm, setShowNewUserForm] = useState(false);
  const [newUserName, setNewUserName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserRole, setNewUserRole] = useState("user");
  const [createdToken, setCreatedToken] = useState<string | null>(null);
  const [managingGroupsFor, setManagingGroupsFor] = useState<User | null>(null);

  const { data: users, isLoading } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: api.listUsers,
    refetchInterval: 5000,
  });

  const { data: allGroups } = useQuery({
    queryKey: ["admin", "groups"],
    queryFn: api.listGroups,
  });

  const { data: userGroups } = useQuery({
    queryKey: ["admin", "users", managingGroupsFor?.user_id, "groups"],
    queryFn: () => (managingGroupsFor ? api.getUserGroups(managingGroupsFor.user_id) : Promise.resolve([])),
    enabled: !!managingGroupsFor,
  });

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = await api.createUser({
        name: newUserName,
        email: newUserEmail || undefined,
        role: newUserRole,
      });
      setCreatedToken(data.token);
      setNewUserName("");
      setNewUserEmail("");
      setNewUserRole("user");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    } catch (err) {
      console.error(`Failed to create user: ${err}`);
    }
  };

  const handleDeactivate = async (userId: string, name: string) => {
    if (!window.confirm(`Deactivate user "${name}"?`)) return;
    try {
      const res = await api.deactivateUser(userId);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    } catch (err) {
      console.error(`Failed to deactivate user: ${err}`);
    }
  };

  const handleAddToGroup = async (groupId: string) => {
    if (!managingGroupsFor) return;
    try {
      const res = await api.addUserToGroup(managingGroupsFor.user_id, groupId);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      queryClient.invalidateQueries({ queryKey: ["admin", "users", managingGroupsFor.user_id, "groups"] });
    } catch (err) {
      console.error(`Failed to add to group: ${err}`);
    }
  };

  const handleRemoveFromGroup = async (groupId: string) => {
    if (!managingGroupsFor) return;
    try {
      const res = await api.removeUserFromGroup(managingGroupsFor.user_id, groupId);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      queryClient.invalidateQueries({ queryKey: ["admin", "users", managingGroupsFor.user_id, "groups"] });
    } catch (err) {
      console.error(`Failed to remove from group: ${err}`);
    }
  };

  const userGroupIds = new Set(userGroups?.map((g) => g.group_id) || []);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-medium">Users</h1>
        <button
          onClick={() => setShowNewUserForm(true)}
          className="px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-hover transition-colors"
        >
          New User
        </button>
      </div>

      {showNewUserForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-elevated p-6 rounded-lg border border-border w-96">
            <h2 className="text-lg font-medium mb-4">Create New User</h2>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  className="w-full px-3 py-2 bg-input border border-border rounded-md text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email (optional)</label>
                <input
                  type="email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-input border border-border rounded-md text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Role</label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value)}
                  className="w-full px-3 py-2 bg-input border border-border rounded-md text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewUserForm(false)}
                  className="flex-1 px-4 py-2 border border-border rounded-md text-muted-foreground hover:bg-subtle hover:text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-hover"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {createdToken && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-elevated p-6 rounded-lg border border-border w-96">
            <h2 className="text-lg font-medium mb-2">User Created</h2>
            <p className="text-sm text-amber-600 mb-4">
              Copy this token now — it won&apos;t be shown again!
            </p>
            <div className="bg-input border border-border p-3 rounded-md font-mono text-xs break-all mb-4 text-primary">
              {createdToken}
            </div>
            <button
              onClick={() => setCreatedToken(null)}
              className="w-full px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-hover"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {managingGroupsFor && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-elevated p-6 rounded-lg border border-border w-96 max-h-[80vh] overflow-y-auto">
            <h2 className="text-lg font-medium mb-4">
              Manage Groups for {managingGroupsFor.name}
            </h2>
            <div className="space-y-2">
              {allGroups?.map((group) => (
                <div
                  key={group.group_id}
                  className="flex items-center justify-between p-2 border rounded-md"
                >
                  <span className="text-sm">{group.name}</span>
                  {userGroupIds.has(group.group_id) ? (
                    <button
                      onClick={() => handleRemoveFromGroup(group.group_id)}
                      className="text-xs text-destructive hover:text-red-300 transition-colors"
                    >
                      Remove
                    </button>
                  ) : (
                    <button
                      onClick={() => handleAddToGroup(group.group_id)}
                      className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      Add
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={() => setManagingGroupsFor(null)}
              className="w-full mt-4 px-4 py-2 border border-border rounded-md text-muted-foreground hover:bg-subtle hover:text-primary transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="p-8 flex items-center justify-center text-muted-foreground gap-2">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading users...
        </div>
      ) : (
        <div className="bg-elevated rounded-lg border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-subtle text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="px-4 py-3 text-left font-medium">Email</th>
                <th className="px-4 py-3 text-left font-medium">Role</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">User ID</th>
                <th className="px-4 py-3 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users?.map((user) => (
                <tr key={user.user_id} className="hover:bg-subtle">
                  <td className="px-4 py-3 font-medium">{user.name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{user.email || "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        user.role === "admin"
                          ? "bg-purple-900/40 text-purple-300 border border-purple-800/50"
                          : "bg-subtle text-muted-foreground"
                      }`}
                    >
                      {user.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        user.is_active
                          ? "bg-success-dim text-success border border-success/20"
                          : "bg-destructive-dim text-destructive border border-destructive/20"
                      }`}
                    >
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {truncateId(user.user_id)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setManagingGroupsFor(user)}
                        className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        Manage Groups
                      </button>
                      {user.is_active && (
                        <button
                          onClick={() => handleDeactivate(user.user_id, user.name)}
                          className="text-xs text-destructive hover:text-red-300 transition-colors"
                        >
                          Deactivate
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {users?.length === 0 && (
            <div className="p-8 text-center text-muted-foreground">No users</div>
          )}
        </div>
      )}
    </div>
  );
}
