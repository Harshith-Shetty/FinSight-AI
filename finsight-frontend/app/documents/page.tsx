'use client';

import { useAuth } from '@/contexts/AuthContext';
import { DocumentUpload } from '@/components/documents/DocumentUpload';
import { DocumentList } from '@/components/documents/DocumentList';
import { PublicDocumentList } from '@/components/documents/PublicDocumentList';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, UploadCloud } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { uploadPublicDocument } from '@/lib/api';

export default function DocumentsPage() {
    const { isAuthenticated, loading, user, token, isAdmin } = useAuth();
    const router = useRouter();
    const [activeTab, setActiveTab] = useState<'private' | 'public'>('private');
    const [uploadingPublic, setUploadingPublic] = useState(false);

    // Protect the route
    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, loading, router]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    if (!isAuthenticated) return null;

    const handlePublicUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0 || !token) return;
        
        try {
            setUploadingPublic(true);
            const file = e.target.files[0];
            await uploadPublicDocument(file, token);
            toast.success('Public document uploaded successfully');
            window.location.reload(); // Quick refresh for simplicity
        } catch (error) {
            toast.error('Failed to upload public document');
        } finally {
            setUploadingPublic(false);
            e.target.value = ''; // Reset input
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                <div className="flex items-center space-x-4">
                    <Button variant="ghost" size="icon" onClick={() => router.push('/chat')}>
                        <ArrowLeft className="h-6 w-6" />
                    </Button>
                    <h1 className="text-3xl font-bold">Knowledge Base</h1>
                </div>

                <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700 pb-2">
                    <button 
                        className={`text-lg font-medium px-4 py-2 ${activeTab === 'private' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
                        onClick={() => setActiveTab('private')}
                    >
                        My Documents
                    </button>
                    <button 
                        className={`text-lg font-medium px-4 py-2 ${activeTab === 'public' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
                        onClick={() => setActiveTab('public')}
                    >
                        System Knowledge Base
                    </button>
                </div>

                {activeTab === 'private' && (
                    <div className="space-y-6">
                        <p className="text-gray-500 dark:text-gray-400">
                            Upload documents to use in your "Private" and "Hybrid" chats.
                        </p>
                        
                        {user?.role === 'GUEST' ? (
                            <div className="bg-orange-50 border border-orange-200 text-orange-800 p-4 rounded-md">
                                Guest users cannot upload private documents. Please upgrade to a Normal or Premium account.
                            </div>
                        ) : (
                            <DocumentUpload onUploadSuccess={() => window.location.reload()} />
                        )}

                        <DocumentList />
                    </div>
                )}

                {activeTab === 'public' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center">
                            <p className="text-gray-500 dark:text-gray-400 max-w-2xl">
                                Documents in the System Knowledge Base are available to all users across the platform when using "Hybrid" mode.
                            </p>
                            {isAdmin && (
                                <div className="relative">
                                    <input 
                                        type="file" 
                                        id="public-upload" 
                                        className="hidden" 
                                        accept=".pdf,.txt,.docx"
                                        onChange={handlePublicUpload}
                                        disabled={uploadingPublic}
                                    />
                                    <Button asChild disabled={uploadingPublic}>
                                        <label htmlFor="public-upload" className="cursor-pointer flex items-center">
                                            <UploadCloud className="h-4 w-4 mr-2" />
                                            {uploadingPublic ? 'Uploading...' : 'Upload Public Doc'}
                                        </label>
                                    </Button>
                                </div>
                            )}
                        </div>

                        <PublicDocumentList />
                    </div>
                )}
            </div>
        </div>
    );
}
