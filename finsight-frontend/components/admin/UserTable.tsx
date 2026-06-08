import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getUsers, updateUserRole, resetUserTokens } from '@/lib/api';
import { UserAdminResponse, UserRole } from '@/types';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Loader2, RefreshCw, Save } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

interface UserTableProps {
    refreshKey?: number;
}

export function UserTable({ refreshKey = 0 }: UserTableProps) {
    const { token, user: currentUser } = useAuth();
    const [users, setUsers] = useState<UserAdminResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [updatingId, setUpdatingId] = useState<string | null>(null);
    const [selectedRoles, setSelectedRoles] = useState<Record<string, string>>({});

    useEffect(() => {
        if (!token) return;
        getUsers(token)
            .then((data) => {
                setUsers(data);
                const initialRoles: Record<string, string> = {};
                data.forEach(u => {
                    initialRoles[u.id] = u.role;
                });
                setSelectedRoles(initialRoles);
            })
            .catch(() => toast.error('Failed to load users'))
            .finally(() => setLoading(false));
    }, [token, refreshKey]);

    const handleRoleSelect = (userId: string, role: string) => {
        setSelectedRoles(prev => ({ ...prev, [userId]: role }));
    };

    const handleRoleUpdate = async (userId: string) => {
        if (!token) return;
        const newRole = selectedRoles[userId];
        if (!newRole) return;
        
        setUpdatingId(userId);
        try {
            const updatedUser = await updateUserRole(userId, newRole, token);
            setUsers(users.map(u => u.id === userId ? updatedUser : u));
            toast.success('User role updated');
        } catch (error) {
            toast.error('Failed to update role');
        } finally {
            setUpdatingId(null);
        }
    };
    
    const handleResetTokens = async (userId: string) => {
        if (!token) return;
        setUpdatingId(userId);
        try {
            await resetUserTokens(userId, token);
            setUsers(users.map(u => u.id === userId ? { ...u, tokens_used_this_month: 0 } : u));
            toast.success('Tokens reset');
        } catch (error) {
            toast.error('Failed to reset tokens');
        } finally {
            setUpdatingId(null);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
            </div>
        );
    }

    return (
        <div className="border rounded-md bg-white dark:bg-gray-800">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Email</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Tokens This Month</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Last Login</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {users.map((u) => {
                        const currentSelectedRole = selectedRoles[u.id] || u.role;
                        const hasRoleChanged = currentSelectedRole !== u.role;
                        const isUpdating = updatingId === u.id;
                        const isSelf = u.id === currentUser?.id;
                        const isAdmin = u.role.toLowerCase() === 'admin';
                        const canResetTokens = u.tokens_used_this_month > 0 && !isAdmin;

                        return (
                            <TableRow key={u.id}>
                                <TableCell className="font-medium">
                                    {u.email}
                                    {isSelf && (
                                        <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">You</span>
                                    )}
                                </TableCell>
                                <TableCell>
                                    <select
                                        value={currentSelectedRole}
                                        onChange={(e) => handleRoleSelect(u.id, e.target.value)}
                                        disabled={isUpdating || isSelf}
                                        className="p-1 border rounded text-sm bg-transparent"
                                    >
                                        <option value="admin">Admin</option>
                                        <option value="premium">Premium</option>
                                        <option value="normal">Normal</option>
                                        <option value="guest">Guest</option>
                                    </select>
                                </TableCell>
                                <TableCell>
                                    {isAdmin ? 'Unlimited' : u.tokens_used_this_month.toLocaleString()}
                                </TableCell>
                                <TableCell>
                                    {format(new Date(u.created_at), 'MMM d, yyyy')}
                                </TableCell>
                                <TableCell>
                                    {u.last_login ? format(new Date(u.last_login), 'MMM d, yyyy') : 'Never'}
                                </TableCell>
                                <TableCell className="text-right space-x-2">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        disabled={!hasRoleChanged || isUpdating || isSelf}
                                        onClick={() => handleRoleUpdate(u.id)}
                                    >
                                        {isUpdating && hasRoleChanged ? (
                                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                        ) : (
                                            <Save className="w-4 h-4 mr-1" />
                                        )}
                                        Change Role
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        disabled={!canResetTokens || isUpdating || isSelf}
                                        onClick={() => handleResetTokens(u.id)}
                                        className={canResetTokens ? "text-orange-600 border-orange-200 hover:bg-orange-50 dark:hover:bg-orange-900/20" : ""}
                                    >
                                        {isUpdating && !hasRoleChanged ? (
                                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                        ) : (
                                            <RefreshCw className="w-4 h-4 mr-1" />
                                        )}
                                        Reset Tokens
                                    </Button>
                                </TableCell>
                            </TableRow>
                        );
                    })}
                </TableBody>
            </Table>
        </div>
    );
}
