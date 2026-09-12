'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { deleteChat, getTokens } from '@/lib/api';
import { Chat, TokenUsage } from '@/types';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
    PlusCircle,
    MessageSquare,
    Trash2,
    LogOut,
    FileText,
    TrendingUp,
    User,
    X
} from 'lucide-react';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

interface ChatSidebarProps {
    chats: Chat[];
    selectedChat: Chat | null;
    onSelectChat: (chat: Chat) => void;
    onNewChat: (mode: 'HYBRID' | 'PRIVATE') => void;
    onDeleteChat: () => void;
    isOpen?: boolean;
    onClose?: () => void;
}

export function ChatSidebar({
    chats,
    selectedChat,
    onSelectChat,
    onNewChat,
    onDeleteChat,
    isOpen = false,
    onClose,
}: ChatSidebarProps) {
    const { logout, token, isAdmin, isPremium } = useAuth();
    const router = useRouter();
    const [tokenUsage, setTokenUsage] = useState<TokenUsage | null>(null);

    // Fetch token usage periodically or when selectedChat changes
    useEffect(() => {
        if (token) {
            getTokens(token).then(setTokenUsage).catch(console.error);
        }
    }, [token, selectedChat]); // selectedChat changes on navigation, good enough trigger

    const handleDelete = async (chatId: string, e: React.MouseEvent) => {
        e.stopPropagation();

        if (!token) return;

        try {
            await deleteChat(chatId, token);
            toast.success('Chat deleted');
            onDeleteChat();
        } catch (error) {
            toast.error('Failed to delete chat');
        }
    };

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    const handleSelectChat = (chat: Chat) => {
        onSelectChat(chat);
        onClose?.();
    };

    return (
        <>
            {/* Mobile overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={onClose}
                />
            )}

            <div
                className={`
                    fixed md:static inset-y-0 left-0 z-50
                    w-72 sm:w-80 max-w-[85vw]
                    bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
                    h-dvh min-h-0 shrink-0 overflow-y-auto overscroll-contain flex flex-col transform transition-transform duration-200 ease-in-out
                    ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
                `}
            >
            {/* Header */}
            <div className="shrink-0 p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-4">
                    <h1 className="text-xl font-bold">FinSight AI</h1>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="md:hidden"
                        onClick={onClose}
                    >
                        <X className="h-5 w-5" />
                    </Button>
                </div>
                <div className="flex gap-2">
                    <Button
                        onClick={() => { onNewChat('HYBRID'); onClose?.(); }}
                        className="flex-1"
                        size="sm"
                    >
                        <PlusCircle className="mr-2 h-4 w-4" />
                        Hybrid
                    </Button>
                    <Button
                        onClick={() => { onNewChat('PRIVATE'); onClose?.(); }}
                        variant="outline"
                        className="flex-1"
                        size="sm"
                    >
                        <PlusCircle className="mr-2 h-4 w-4" />
                        Private
                    </Button>
                </div>
                <Button
                    variant="ghost"
                    className="w-full justify-start mt-2"
                    onClick={() => window.location.href = '/documents'}
                >
                    <FileText className="mr-2 h-4 w-4" />
                    Manage Documents
                </Button>
                <Button
                    variant="ghost"
                    className={`w-full justify-start mt-2 ${
                        isPremium 
                            ? 'text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20' 
                            : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50'
                    }`}
                    onClick={() => {
                        if (isPremium) {
                            router.push('/analyze');
                        } else {
                            toast.error('Deep Ticker Analysis is a premium feature. Please upgrade your plan.');
                        }
                    }}
                >
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Deep Ticker Analysis
                    {!isPremium && (
                        <span className="ml-auto text-[10px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 px-1.5 py-0.5 rounded-md uppercase tracking-wider">
                            Premium
                        </span>
                    )}
                </Button>
                {isAdmin && (
                    <Button
                        variant="ghost"
                        className="w-full justify-start mt-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                        onClick={() => router.push('/admin')}
                    >
                        <LogOut className="mr-2 h-4 w-4 rotate-180" />
                        Admin Dashboard
                    </Button>
                )}
                <Button
                    variant="ghost"
                    className="w-full justify-start mt-2"
                    onClick={() => router.push('/profile')}
                >
                    <User className="mr-2 h-4 w-4" />
                    My Profile
                </Button>
            </div>

            {/* Chat List */}
            <div className="min-h-24 flex-1 overflow-y-auto overscroll-contain" aria-label="Chat history" tabIndex={0}>
                <div className="p-2">
                    {chats.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                            No chats yet
                        </div>
                    ) : (
                        chats.map((chat) => (
                            <div
                                key={chat.id}
                                onClick={() => handleSelectChat(chat)}
                                role="button" tabIndex={0}
                                onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); handleSelectChat(chat); } }}
                                className={`
                  flex items-center justify-between p-3 mb-2 rounded-lg cursor-pointer
                  transition-colors
                  ${selectedChat?.id === chat.id
                                        ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                                    }
                `}
                            >
                                <div className="flex items-center flex-1 min-w-0">
                                    <MessageSquare className="h-4 w-4 mr-2 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{chat.title}</p>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                            {chat.mode === 'HYBRID' ? '🌐 Hybrid' : '🔒 Private'}
                                        </p>
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    aria-label={`Delete chat: ${chat.title}`}
                                    onClick={(e) => handleDelete(chat.id, e)}
                                    className="ml-2 flex-shrink-0"
                                >
                                    <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Footer with Quota */}
            <div className="shrink-0 p-4 border-t border-gray-200 dark:border-gray-700 flex flex-col gap-4">
                {tokenUsage && !isAdmin && (
                    <div className="flex flex-col gap-2">
                        <div className="flex justify-between text-xs text-gray-500">
                            <span>Token Quota</span>
                            <span className={tokenUsage.is_over_limit ? 'text-red-500 font-bold' : ''}>
                                {tokenUsage.tokens_used.toLocaleString()} / {tokenUsage.limit?.toLocaleString() || '∞'}
                            </span>
                        </div>
                        <Progress 
                            value={tokenUsage.limit ? (tokenUsage.tokens_used / tokenUsage.limit) * 100 : 0} 
                            className={`h-2 ${tokenUsage.is_over_limit ? 'bg-red-200 [&>div]:bg-red-500' : ''}`}
                        />
                    </div>
                )}
                {isAdmin && (
                    <div className="text-xs text-gray-500 text-center italic">
                        Admin: Unlimited Tokens
                    </div>
                )}

                <Button
                    variant="outline"
                    className="w-full"
                    onClick={handleLogout}
                >
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                </Button>
            </div>
            </div>
        </>
    );
}
