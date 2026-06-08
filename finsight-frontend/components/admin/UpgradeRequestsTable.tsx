'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getAdminUpgradeRequests, approveUpgradeRequest } from '@/lib/api';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface UpgradeRequestsTableProps {
    onApprove?: () => void;
}

export function UpgradeRequestsTable({ onApprove }: UpgradeRequestsTableProps) {
    const { token } = useAuth();
    const [requests, setRequests] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState<string | null>(null);

    useEffect(() => {
        if (token) {
            fetchRequests();
        }
    }, [token]);

    const fetchRequests = async () => {
        try {
            const data = await getAdminUpgradeRequests(token!);
            setRequests(data);
        } catch (error) {
            toast.error('Failed to load upgrade requests');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (id: string) => {
        setProcessingId(id);
        try {
            await approveUpgradeRequest(id, token!);
            toast.success('Upgrade request approved');
            fetchRequests();
            if (onApprove) onApprove();
        } catch (error: any) {
            toast.error(error.message || 'Failed to approve request');
        } finally {
            setProcessingId(null);
        }
    };

    if (loading) {
        return (
            <Card className="p-8 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </Card>
        );
    }

    if (requests.length === 0) {
        return (
            <Card className="p-8 text-center text-gray-500">
                No pending upgrade requests.
            </Card>
        );
    }

    return (
        <Card className="overflow-hidden">
            <div className="overflow-x-auto">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Date</TableHead>
                            <TableHead>User Email</TableHead>
                            <TableHead className="w-1/2">Reason</TableHead>
                            <TableHead className="text-right">Action</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {requests.map((req) => (
                            <TableRow key={req.id}>
                                <TableCell className="whitespace-nowrap">
                                    {new Date(req.created_at).toLocaleDateString()}
                                </TableCell>
                                <TableCell className="font-medium">{req.email}</TableCell>
                                <TableCell>
                                    <div className="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-md text-sm italic">
                                        "{req.reason}"
                                    </div>
                                </TableCell>
                                <TableCell className="text-right">
                                    <Button
                                        size="sm"
                                        onClick={() => handleApprove(req.id)}
                                        disabled={processingId === req.id}
                                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                                    >
                                        {processingId === req.id ? (
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        ) : (
                                            <CheckCircle2 className="w-4 h-4 mr-2" />
                                        )}
                                        Approve
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </Card>
    );
}
