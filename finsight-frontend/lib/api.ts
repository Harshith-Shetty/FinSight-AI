import { AuthResponse, Chat, ChatCreate, ChatHistoryResponse, Document, DocumentUploadResponse, Message, MessageCreate, SSEChunk, TokenUsage, PublicDocument, UserAdminResponse, UserRole } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── 401 interceptor ─────────────────────────────────────────────────────────
// AuthProvider calls setLogoutCallback() on mount so this module can trigger
// logout + redirect without importing React hooks here.
let _logoutCallback: (() => void) | null = null;
export function setLogoutCallback(fn: () => void) {
    _logoutCallback = fn;
}

async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const res = await fetch(url, options);
    if (res.status === 401) {
        // Token expired or invalid — clear session and redirect
        if (_logoutCallback) _logoutCallback();
    }
    return res;
}
// ─────────────────────────────────────────────────────────────────────────────

// Auth API
export async function register(email: string, password: string): Promise<{ email: string; email_verification_required: boolean; message: string }> {
    const res = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Registration failed');
    }

    return res.json();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Login failed');
    }

    return res.json();
}

export async function verifyEmail(email: string, otp: string): Promise<AuthResponse> {
    const res = await fetch(`${API_URL}/api/v1/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp })
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Verification failed');
    }

    return res.json();
}

export async function resendOTP(email: string, purpose: string = 'email_verification'): Promise<{ message: string }> {
    const res = await fetch(`${API_URL}/api/v1/auth/resend-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, purpose })
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to resend code');
    }

    return res.json();
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
    const res = await fetch(`${API_URL}/api/v1/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to send reset code');
    }

    return res.json();
}

export async function resetPassword(email: string, otp: string, newPassword: string): Promise<{ message: string }> {
    const res = await fetch(`${API_URL}/api/v1/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp, new_password: newPassword })
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to reset password');
    }

    return res.json();
}

export async function getCurrentUser(token: string): Promise<any> {
    const res = await apiFetch(`${API_URL}/api/v1/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!res.ok) {
        throw new Error('Failed to get user');
    }

    return res.json();
}

export async function getTokens(token: string): Promise<TokenUsage> {
    const res = await apiFetch(`${API_URL}/api/v1/auth/me/tokens`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to get token usage');
    return res.json();
}

// Chat API
export async function getChats(token: string): Promise<Chat[]> {
    const res = await apiFetch(`${API_URL}/api/v1/chats`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch chats');
    return res.json();
}

export async function createChat(data: ChatCreate, token: string): Promise<Chat> {
    console.log('Creating chat with:', { mode: data.mode, apiUrl: API_URL });

    const res = await apiFetch(`${API_URL}/api/v1/chats`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });

    console.log('Create chat response:', { status: res.status, ok: res.ok });

    if (!res.ok) {
        const errorText = await res.text();
        console.error('Create chat error:', errorText);
        throw new Error(`Failed to create chat: ${errorText}`);
    }

    const result = await res.json();
    console.log('Chat created successfully:', result);
    return result;
}

export async function deleteChat(chatId: string, token: string): Promise<void> {
    const res = await apiFetch(`${API_URL}/api/v1/chats/${chatId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to delete chat');
}

// Message API
export async function getChatMessages(chatId: string, token: string): Promise<Message[]> {
    const res = await apiFetch(`${API_URL}/api/v1/chats/${chatId}/messages`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch messages');
    return res.json();
}

export async function sendMessage(
    chatId: string,
    data: MessageCreate,
    token: string
): Promise<ChatHistoryResponse> {
    const res = await apiFetch(`${API_URL}/api/v1/chats/${chatId}/messages`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        throw new Error('Failed to send message');
    }

    return res.json();
}

// SSE Streaming — uses fetch + ReadableStream so we can send Authorization header
export async function* streamMessage(
    chatId: string,
    content: string,
    token: string
): AsyncGenerator<SSEChunk> {
    const res = await apiFetch(`${API_URL}/api/v1/chats/${chatId}/messages/stream`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
    });

    if (!res.ok) {
        throw new Error(`Stream failed: ${res.status}`);
    }

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    yield JSON.parse(line.slice(6)) as SSEChunk;
                } catch {
                    // skip malformed lines
                }
            }
        }
    }
}

// Document API
export async function getDocuments(token: string): Promise<Document[]> {
    const res = await apiFetch(`${API_URL}/api/v1/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
}

export async function uploadDocument(file: File, token: string): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await apiFetch(`${API_URL}/api/v1/documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });

    if (!res.ok) {
        throw new Error('Failed to upload document');
    }

    return res.json();
}

export async function deleteDocument(documentId: string, token: string): Promise<void> {
    const res = await apiFetch(`${API_URL}/api/v1/documents/${documentId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to delete document');
}

export async function reprocessDocument(documentId: string, token: string): Promise<Document> {
    const res = await apiFetch(`${API_URL}/api/v1/documents/${documentId}/reprocess`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to reprocess document');
    }
    return res.json();
}

// Public Document API
export async function getPublicDocuments(token: string): Promise<PublicDocument[]> {
    const res = await apiFetch(`${API_URL}/api/v1/public-documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch public documents');
    return res.json();
}

export async function uploadPublicDocument(file: File, token: string): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiFetch(`${API_URL}/api/v1/public-documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!res.ok) throw new Error('Failed to upload public document');
    return res.json();
}

export async function deletePublicDocument(documentId: string, token: string): Promise<void> {
    const res = await apiFetch(`${API_URL}/api/v1/public-documents/${documentId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to delete public document');
}

// Admin API
export async function getUsers(token: string): Promise<UserAdminResponse[]> {
    const res = await apiFetch(`${API_URL}/api/v1/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
}

export async function updateUserRole(userId: string, role: string, token: string): Promise<UserAdminResponse> {
    const res = await apiFetch(`${API_URL}/api/v1/admin/users/${userId}/role`, {
        method: 'PUT',
        headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ role })
    });
    if (!res.ok) throw new Error('Failed to update user role');
    return res.json();
}

export async function resetUserTokens(userId: string, token: string): Promise<any> {
    const res = await apiFetch(`${API_URL}/api/v1/admin/users/${userId}/reset-tokens`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to reset tokens');
    return res.json();
}

export async function getSystemStats(token: string): Promise<any> {
    const res = await apiFetch(`${API_URL}/api/v1/admin/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
}

export async function submitAnalysis(
    ticker: string,
    focusArea: string,
    filingYear: number,
    token: string
): Promise<{ task_id: string; status: string; message: string }> {
    const res = await apiFetch(`${API_URL}/api/v1/analyze`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ticker,
            focus_area: focusArea,
            filing_year: filingYear
        })
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to submit analysis');
    }

    return res.json();
}

export async function getTaskStatus(taskId: string, token: string): Promise<any> {
    const res = await apiFetch(`${API_URL}/api/v1/tasks/${taskId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to fetch task status');
    }

    return res.json();
}

// User Profile & Upgrades
export async function getMyProfile(token: string): Promise<any> {
    const res = await apiFetch(`${API_URL}/api/v1/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
}

export async function requestPlanUpgrade(reason: string, token: string): Promise<any> {
    const res = await apiFetch(`${API_URL}/api/v1/users/upgrade-request`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason })
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to request upgrade');
    }
    return res.json();
}

// Admin Upgrade Requests
export async function getAdminUpgradeRequests(token: string): Promise<any[]> {
    const res = await apiFetch(`${API_URL}/api/v1/admin/upgrade-requests`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch upgrade requests');
    return res.json();
}

export async function approveUpgradeRequest(requestId: string, token: string): Promise<any> {
    const res = await apiFetch(`${API_URL}/api/v1/admin/upgrade-requests/${requestId}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to approve request');
    return res.json();
}

export async function resendWelcomeEmail(email: string, token: string): Promise<any> {
    const res = await apiFetch(`${API_URL}/api/v1/auth/resend-welcome`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to resend welcome email');
    }
    return res.json();
}
