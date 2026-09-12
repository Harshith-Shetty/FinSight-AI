'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getChatMessages, streamMessage } from '@/lib/api';
import { Chat, Message, SSEChunk, Source } from '@/types';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';
import { toast } from 'sonner';

interface ChatWindowProps {
    chat: Chat;
    onMessageSent?: () => void;  // Called after a message completes — lets parent refresh chat list/title
    onOpenSidebar?: () => void;
}

export function ChatWindow({ chat, onMessageSent, onOpenSidebar }: ChatWindowProps) {
    const { token } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [streaming, setStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const [streamingSources, setStreamingSources] = useState<Source[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);
    const followLatest = useRef(true);
    const [showLatest, setShowLatest] = useState(false);

    useEffect(() => {
        loadMessages();
    }, [chat.id]);

    useEffect(() => {
        // Auto-scroll to bottom
        if (scrollRef.current && followLatest.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, streamingContent]);

    const loadMessages = async () => {
        if (!token) return;

        try {
            const data = await getChatMessages(chat.id, token);
            setMessages(data);
        } catch (error) {
            toast.error('Failed to load messages');
        } finally {
            setLoading(false);
        }
    };

    const handleSendMessage = async (content: string) => {
        if (!token || !content.trim()) return;

        followLatest.current = true;
        setShowLatest(false);
        // Add user message immediately
        const userMessage: Message = {
            id: 'temp-' + Date.now(),
            role: 'user',
            content,
            created_at: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setStreaming(true);
        setStreamingSources([]);
        setStreamingContent('');

        try {
            let fullResponse = '';
            let sources: SSEChunk['sources'] = [];
            let assistantMessageId = '';

            for await (const chunk of streamMessage(chat.id, content, token)) {
                if (chunk.type === 'error') throw new Error(chunk.error || 'The answer could not be completed. Please try again.');
                if (chunk.type === 'chunk' && chunk.content) {
                    fullResponse += chunk.content;
                    setStreamingContent(fullResponse);
                } else if (chunk.type === 'sources') {
                    sources = chunk.sources;
                    setStreamingSources(chunk.sources ?? []);
                } else if (chunk.type === 'done') {
                    assistantMessageId = chunk.message_id ?? 'assistant-' + Date.now();
                }
            }

            // Replace temp user message + add final assistant message
            const assistantMessage: Message = {
                id: assistantMessageId,
                role: 'assistant',
                content: fullResponse,
                metadata: { sources: sources ?? [], mode: chat.mode },
                created_at: new Date().toISOString(),
            };

            setMessages((prev) => [
                ...prev.filter((m) => m.id !== userMessage.id),
                { ...userMessage, id: 'user-' + Date.now() },
                assistantMessage,
            ]);
            setStreamingContent('');
        } catch (error: any) {
            toast.error(error.message || 'Failed to send message');
            // Remove temp message on error
            setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
        } finally {
            setStreaming(false);
            setStreamingContent('');
            // Notify parent so sidebar can refresh title
            onMessageSent?.();
        }
    };

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    return (
        <div className="relative flex-1 min-h-0 min-w-0 flex flex-col bg-white dark:bg-gray-800">
            {/* Header */}
            <div className="shrink-0 p-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                <Button
                    variant="ghost"
                    size="icon"
                    className="md:hidden -ml-2 flex-shrink-0"
                    aria-label="Open chat sidebar"
                    onClick={onOpenSidebar}
                >
                    <Menu className="h-5 w-5" />
                </Button>
                <div className="min-w-0">
                    <h2 className="text-lg font-semibold truncate">{chat.title}</h2>
                    <p className="text-sm text-gray-500">
                        {chat.mode === 'HYBRID' ? '🌐 Hybrid Mode' : '🔒 Private Mode'}
                    </p>
                </div>
            </div>

            {/* Messages */}
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-3 sm:p-6" ref={scrollRef}
                tabIndex={0} role="region" aria-label="Conversation"
                onScroll={(event) => {
                    const el = event.currentTarget;
                    followLatest.current = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
                    setShowLatest(!followLatest.current);
                }}>
                <div className="space-y-4 max-w-4xl mx-auto">
                    {messages.map((message) => (
                        <MessageBubble key={message.id} message={message} />
                    ))}

                    {/* Streaming message */}
                    {streaming && streamingContent && (
                        <MessageBubble
                            message={{
                                id: 'streaming',
                                role: 'assistant',
                                content: streamingContent,
                                metadata: { sources: streamingSources, mode: chat.mode },
                                created_at: new Date().toISOString(),
                            }}
                        />
                    )}

                    {/* Loading indicator */}
                    {streaming && !streamingContent && (
                        <div className="flex items-center text-gray-500">
                            <div className="animate-pulse">AI is thinking...</div>
                        </div>
                    )}
                </div>
            </div>
            {showLatest && <Button variant="outline" className="absolute bottom-28 left-1/2 -translate-x-1/2 shadow-md" onClick={() => { followLatest.current = true; setShowLatest(false); scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'instant' }); }}>Jump to latest</Button>}

            {/* Input */}
            <div className="shrink-0 p-3 sm:p-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] border-t border-gray-200 dark:border-gray-700">
                <MessageInput onSend={handleSendMessage} disabled={streaming} />
            </div>
        </div>
    );
}
