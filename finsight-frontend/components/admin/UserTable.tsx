import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getUsers, updateUserRole } from '@/lib/api';
import { UserAdminResponse, UserRole } from '@/types';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

export function UserTable() {
    const { token, user: currentUser } = useAuth();
    const [users, setUsers] = useState<UserAdminResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [updatingId, setUpdatingId] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;
        getUsers(token)
            .then(setUsers)
            .catch(() => toast.error('Failed to load users'))
            .finally(() => setLoading(false));
    }, [token]);

    const handleRoleChange = async (userId: string, newRole: UserRole) => {
        if (!token) return;
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
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {users.map((u) => (
                        <TableRow key={u.id}>
                            <TableCell className="font-medium">
                                {u.email}
                                {u.id === currentUser?.id && (
                                    <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">You</span>
                                )}
                            </TableCell>
                            <TableCell>
                                <select
                                    value={u.role}
                                    onChange={(e) => handleRoleChange(u.id, e.target.value as UserRole)}
                                    disabled={updatingId === u.id || u.id === currentUser?.id}
                                    className="p-1 border rounded text-sm bg-transparent"
                                >
                                    <option value="ADMIN">Admin</option>
                                    <option value="PREMIUM">Premium</option>
                                    <option value="NORMAL">Normal</option>
                                    <option value="GUEST">Guest</option>
                                </select>
                                {updatingId === u.id && <Loader2 className="inline h-3 w-3 ml-2 animate-spin" />}
                            </TableCell>
                            <TableCell>
                                {u.tokens_used_this_month.toLocaleString()}
                            </TableCell>
                            <TableCell>
                                {format(new Date(u.created_at), 'MMM d, yyyy')}
                            </TableCell>
                            <TableCell>
                                {u.last_login ? format(new Date(u.last_login), 'MMM d, yyyy') : 'Never'}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}
