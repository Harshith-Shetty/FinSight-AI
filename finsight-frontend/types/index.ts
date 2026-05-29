export type UserRole = 'ADMIN' | 'PREMIUM' | 'NORMAL' | 'GUEST';

export interface User {
    id: string;
    email: string;
    role: UserRole;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
}

export interface Chat {
    id: string;
    title: string;
    mode: 'HYBRID' | 'PRIVATE';
    created_at: string;
    updated_at: string;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    metadata?: {
        sources?: Source[];
        mode?: string;
    };
    created_at: string;
}

export interface Source {
    text: string;
    score: number;
    source: 'user' | 'system';
    document_id?: string;
    metadata?: any;
}

export interface Document {
    id: string;
    filename: string;
    file_size: number | null;
    file_type: string | null;
    processing_status: 'pending' | 'processing' | 'completed' | 'failed';
    upload_date: string;
    is_system_doc?: boolean;
}

export interface PublicDocument {
    id: string;
    filename: string;
    file_size: number | null;
    file_type: string | null;
    upload_date: string;
    user_id: string;
}

export interface TokenUsage {
    month: string;
    tokens_used: number;
    limit: number | null;
    remaining: number | null;
    is_over_limit: boolean;
}

export interface UserAdminResponse {
    id: string;
    email: string;
    role: UserRole;
    created_at: string;
    last_login: string | null;
    tokens_used_this_month: number;
}

export interface DocumentUploadResponse {
    id: string;
    filename: string;
    file_size: number | null;
    processing_status: 'pending' | 'processing' | 'completed' | 'failed';
    upload_date: string;
}

export interface ChatCreate {
    mode: 'HYBRID' | 'PRIVATE';
    title?: string;
}

export interface MessageCreate {
    content: string;
}

export interface ChatHistoryResponse {
    chat_id: string;
    messages: Message[];
}

export interface SSEChunk {
    type: 'user_message' | 'chunk' | 'sources' | 'done';
    content?: string;
    message_id?: string;
    sources?: Source[];
}
