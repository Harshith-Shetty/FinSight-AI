import { useState, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { uploadDocument } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Upload, X, FileText, Loader2, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { Progress } from '@/components/ui/progress';

interface DocumentUploadProps {
    onUploadSuccess: () => void;
}

export function DocumentUpload({ onUploadSuccess }: DocumentUploadProps) {
    const { token } = useAuth();
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            validateAndSetFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const validateAndSetFile = (file: File) => {
        // Check file type
        const validTypes = [
            'application/pdf',
            'text/plain',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
            'text/markdown'
        ];

        // Check extension as fallback
        const validExtensions = ['.pdf', '.txt', '.docx', '.md'];
        const extension = '.' + file.name.split('.').pop()?.toLowerCase();

        if (!validTypes.includes(file.type) && !validExtensions.includes(extension)) {
            toast.error('Invalid file type. Please upload PDF, DOCX, TXT, or MD.');
            return;
        }

        // Check file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            toast.error('File too large. Maximum size is 10MB.');
            return;
        }

        setSelectedFile(file);
    };

    const handleUpload = async () => {
        if (!selectedFile || !token) return;

        setUploading(true);
        setProgress(10); // Start progress

        try {
            // Simulate progress (since fetch doesn't give us upload progress easily)
            const progressInterval = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);

            await uploadDocument(selectedFile, token);

            clearInterval(progressInterval);
            setProgress(100);

            toast.success('Document uploaded successfully');
            setSelectedFile(null);
            onUploadSuccess();
        } catch (error: any) {
            toast.error(error.message || 'Failed to upload document');
            setProgress(0);
        } finally {
            setUploading(false);
            // Reset progress after a moment
            setTimeout(() => setProgress(0), 1000);
        }
    };

    return (
        <Card>
            <CardContent className="p-6">
                <div
                    className={`
                        border-2 border-dashed rounded-lg p-8 text-center transition-colors
                        ${dragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-700'}
                        ${uploading ? 'opacity-50 pointer-events-none' : ''}
                    `}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                >
                    <input
                        ref={inputRef}
                        type="file"
                        className="hidden"
                        onChange={handleChange}
                        accept=".pdf,.docx,.txt,.md"
                    />

                    {!selectedFile ? (
                        <div className="flex flex-col items-center justify-center space-y-4">
                            <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full">
                                <Upload className="h-8 w-8 text-gray-500" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold">Upload a document</h3>
                                <p className="text-sm text-gray-500 mt-1">
                                    Drag and drop or click to select
                                </p>
                            </div>
                            <p className="text-xs text-gray-400">
                                Supports PDF, DOCX, TXT, MD (Max 10MB)
                            </p>
                            <Button
                                variant="outline"
                                onClick={() => inputRef.current?.click()}
                            >
                                Select File
                            </Button>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center space-y-4">
                            <div className="flex items-center space-x-4 w-full max-w-md bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                <FileText className="h-8 w-8 text-blue-500 flex-shrink-0" />
                                <div className="flex-1 min-w-0 text-left">
                                    <p className="font-medium truncate">{selectedFile.name}</p>
                                    <p className="text-sm text-gray-500">
                                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                </div>
                                {!uploading && (
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setSelectedFile(null)}
                                        className="flex-shrink-0"
                                    >
                                        <X className="h-4 w-4" />
                                    </Button>
                                )}
                            </div>

                            {uploading && (
                                <div className="w-full max-w-md space-y-2">
                                    <Progress value={progress} className="h-2" />
                                    <p className="text-sm text-gray-500">Uploading...</p>
                                </div>
                            )}

                            {!uploading && (
                                <div className="flex gap-2">
                                    <Button onClick={handleUpload} disabled={uploading}>
                                        <Upload className="h-4 w-4 mr-2" />
                                        Upload File
                                    </Button>
                                    <Button variant="ghost" onClick={() => setSelectedFile(null)}>
                                        Cancel
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
