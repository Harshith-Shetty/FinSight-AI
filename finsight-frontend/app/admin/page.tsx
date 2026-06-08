'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SystemStats } from '@/components/admin/SystemStats';
import { UserTable } from '@/components/admin/UserTable';
import { UpgradeRequestsTable } from '@/components/admin/UpgradeRequestsTable';

export default function AdminDashboardPage() {
    const { isAuthenticated, loading, isAdmin } = useAuth();
    const router = useRouter();

    // Protect the route: Only Admins allowed
    useEffect(() => {
        if (!loading) {
            if (!isAuthenticated) {
                router.push('/login');
            } else if (!isAdmin) {
                router.push('/chat');
            }
        }
    }, [isAuthenticated, isAdmin, loading, router]);

    if (loading || !isAdmin) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                <div className="flex items-center space-x-4 mb-8">
                    <Button variant="ghost" size="icon" onClick={() => router.push('/chat')}>
                        <ArrowLeft className="h-6 w-6" />
                    </Button>
                    <h1 className="text-3xl font-bold">Admin Dashboard</h1>
                </div>

                <div className="space-y-12">
                    <section>
                        <h2 className="text-2xl font-semibold mb-6">System Statistics</h2>
                        <SystemStats />
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-6">User Management</h2>
                        <UserTable />
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-6">Pending Plan Upgrades</h2>
                        <UpgradeRequestsTable />
                    </section>
                </div>
            </div>
        </div>
    );
}
