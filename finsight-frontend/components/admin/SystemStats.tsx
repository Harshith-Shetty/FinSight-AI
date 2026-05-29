import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getSystemStats } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Loader2, Users, FileText, Database, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';

export function SystemStats() {
    const { token } = useAuth();
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token) return;
        getSystemStats(token)
            .then(setStats)
            .catch(() => toast.error('Failed to load system stats'))
            .finally(() => setLoading(false));
    }, [token]);

    if (loading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
            </div>
        );
    }

    if (!stats) return null;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6 flex flex-col items-center justify-center space-y-2 text-center">
                <Users className="h-8 w-8 text-blue-500 mb-2" />
                <h3 className="text-2xl font-bold">{stats.total_users}</h3>
                <p className="text-sm text-gray-500">Total Users</p>
                <div className="text-xs text-gray-400 mt-2 flex gap-2">
                    <span>A: {stats.users_by_role?.ADMIN || 0}</span>
                    <span>P: {stats.users_by_role?.PREMIUM || 0}</span>
                    <span>N: {stats.users_by_role?.NORMAL || 0}</span>
                    <span>G: {stats.users_by_role?.GUEST || 0}</span>
                </div>
            </Card>

            <Card className="p-6 flex flex-col items-center justify-center space-y-2 text-center">
                <FileText className="h-8 w-8 text-green-500 mb-2" />
                <h3 className="text-2xl font-bold">{stats.total_private_documents}</h3>
                <p className="text-sm text-gray-500">Private Documents</p>
            </Card>

            <Card className="p-6 flex flex-col items-center justify-center space-y-2 text-center">
                <Database className="h-8 w-8 text-purple-500 mb-2" />
                <h3 className="text-2xl font-bold">{stats.total_public_documents}</h3>
                <p className="text-sm text-gray-500">System KB Documents</p>
            </Card>

            <Card className="p-6 flex flex-col items-center justify-center space-y-2 text-center">
                <MessageSquare className="h-8 w-8 text-orange-500 mb-2" />
                <h3 className="text-2xl font-bold">{stats.total_tokens_this_month.toLocaleString()}</h3>
                <p className="text-sm text-gray-500">Tokens Consumed ({stats.month})</p>
            </Card>
        </div>
    );
}
