import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getDocuments, deleteDocument, reprocessDocument } from '@/lib/api';
import { Document } from '@/types';
import { Button } from '@/components/ui/button';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Trash2, FileText, Loader2, RefreshCw, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

export function DocumentList() {
    const { token } = useAuth();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const [retryingId, setRetryingId] = useState<string | null>(null);
    const documentsRef = useRef<Document[]>([]);

    const loadDocuments = async () => {
        if (!token) return;
        try {
            setLoading(true);
            const data = await getDocuments(token);
            setDocuments(data);
            documentsRef.current = data;
        } catch (error) {
            toast.error('Failed to load documents');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDocuments();
        const interval = setInterval(() => {
            const hasProcessing = documentsRef.current.some(
                doc => doc.processing_status === 'pending' || doc.processing_status === 'processing'
            );
            if (hasProcessing) loadDocuments();
        }, 5000);
        return () => clearInterval(interval);
    }, [token]);

    const handleDelete = async (id: string) => {
        if (!token) return;
        if (!confirm('Are you sure you want to delete this document?')) return;
        try {
            setDeletingId(id);
            await deleteDocument(id, token);
            setDocuments(prev => prev.filter(doc => doc.id !== id));
            toast.success('Document deleted');
        } catch {
            toast.error('Failed to delete document');
        } finally {
            setDeletingId(null);
        }
    };

    const handleRetry = async (id: string) => {
        if (!token) return;
        try {
            setRetryingId(id);
            await reprocessDocument(id, token);
            setDocuments(prev =>
                prev.map(doc => doc.id === id ? { ...doc, processing_status: 'pending' } : doc)
            );
            toast.success('Document re-queued for processing');
        } catch (error: any) {
            toast.error(error.message || 'Failed to retry document');
        } finally {
            setRetryingId(null);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-600 dark:text-green-400';
            case 'failed': return 'text-red-600 dark:text-red-400';
            case 'processing': return 'text-blue-600 dark:text-blue-400';
            default: return 'text-gray-500';
        }
    };

    if (loading && documents.length === 0) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">Your Documents</h2>
                <Button variant="outline" size="sm" onClick={loadDocuments} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </Button>
            </div>

            {documents.length === 0 ? (
                <div className="text-center p-8 border rounded-lg border-dashed text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No documents uploaded yet.</p>
                </div>
            ) : (
                <div className="border rounded-md">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Filename</TableHead>
                                <TableHead>Size</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Uploaded</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {documents.map((doc) => (
                                <TableRow key={doc.id}>
                                    <TableCell className="max-w-64 whitespace-normal break-words font-medium [overflow-wrap:anywhere]">
                                        <FileText className="inline h-4 w-4 mr-2 text-blue-500" />
                                        {doc.filename}
                                    </TableCell>
                                    <TableCell>
                                        {doc.file_size != null ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'Unknown'}
                                    </TableCell>
                                    <TableCell className={getStatusColor(doc.processing_status)}>
                                        <span className="capitalize flex items-center">
                                            {doc.processing_status === 'processing' && (
                                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                            )}
                                            {doc.processing_status}
                                        </span>
                                    </TableCell>
                                    <TableCell>
                                        {format(new Date(doc.upload_date), 'MMM d, yyyy')}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-1">
                                            {doc.processing_status === 'failed' && (
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    title="Retry processing"
                                                    className="text-amber-500 hover:text-amber-700 hover:bg-amber-50 dark:hover:bg-amber-900/20"
                                                    onClick={() => handleRetry(doc.id)}
                                                    disabled={retryingId === doc.id}
                                                >
                                                    {retryingId === doc.id
                                                        ? <Loader2 className="h-4 w-4 animate-spin" />
                                                        : <RotateCcw className="h-4 w-4" />
                                                    }
                                                </Button>
                                            )}
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                                                onClick={() => handleDelete(doc.id)}
                                                disabled={deletingId === doc.id}
                                            >
                                                {deletingId === doc.id
                                                    ? <Loader2 className="h-4 w-4 animate-spin" />
                                                    : <Trash2 className="h-4 w-4" />
                                                }
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            )}
        </div>
    );
}
