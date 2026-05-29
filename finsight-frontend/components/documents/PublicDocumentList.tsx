import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getPublicDocuments, deletePublicDocument } from '@/lib/api';
import { PublicDocument } from '@/types';
import { Button } from '@/components/ui/button';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Trash2, FileText, Loader2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

export function PublicDocumentList() {
    const { token, isAdmin } = useAuth();
    const [documents, setDocuments] = useState<PublicDocument[]>([]);
    const [loading, setLoading] = useState(true);
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const loadDocuments = async () => {
        if (!token) return;
        try {
            setLoading(true);
            const data = await getPublicDocuments(token);
            setDocuments(data);
        } catch (error) {
            toast.error('Failed to load public documents');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDocuments();
    }, [token]);

    const handleDelete = async (id: string) => {
        if (!token) return;
        if (!confirm('Are you sure you want to delete this public document? This affects all users.')) return;

        try {
            setDeletingId(id);
            await deletePublicDocument(id, token);
            setDocuments(documents.filter(doc => doc.id !== id));
            toast.success('Public document deleted');
        } catch (error) {
            toast.error('Failed to delete public document');
        } finally {
            setDeletingId(null);
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
                <h2 className="text-xl font-semibold">System Knowledge Base</h2>
                <Button variant="outline" size="sm" onClick={loadDocuments} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </Button>
            </div>

            {documents.length === 0 ? (
                <div className="text-center p-8 border rounded-lg border-dashed text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No public documents uploaded yet.</p>
                </div>
            ) : (
                <div className="border rounded-md">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Filename</TableHead>
                                <TableHead>Size</TableHead>
                                <TableHead>Uploaded</TableHead>
                                {isAdmin && <TableHead className="text-right">Actions</TableHead>}
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {documents.map((doc) => (
                                <TableRow key={doc.id}>
                                    <TableCell className="font-medium flex items-center">
                                        <FileText className="h-4 w-4 mr-2 text-purple-500" />
                                        {doc.filename}
                                    </TableCell>
                                    <TableCell>
                                        {doc.file_size != null ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'Unknown'}
                                    </TableCell>
                                    <TableCell>
                                        {format(new Date(doc.upload_date), 'MMM d, yyyy')}
                                    </TableCell>
                                    {isAdmin && (
                                        <TableCell className="text-right">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                                                onClick={() => handleDelete(doc.id)}
                                                disabled={deletingId === doc.id}
                                            >
                                                {deletingId === doc.id ? (
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                ) : (
                                                    <Trash2 className="h-4 w-4" />
                                                )}
                                            </Button>
                                        </TableCell>
                                    )}
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            )}
        </div>
    );
}
