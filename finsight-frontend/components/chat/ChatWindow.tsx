'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getChatMessages, streamMessage } from '@/lib/api';
import { Chat, Message, SSEChunk } from '@/types';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';

interface ChatWindowProps {
    chat: Chat;
    onMessageSent?: () => void;  // Called after a message completes — lets parent refresh chat list/title
}

export function ChatWindow({ chat, onMessageSent }: ChatWindowProps) {
    const { token } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [streaming, setStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        loadMessages();
    }, [chat.id]);

    useEffect(() => {
        // Auto-scroll to bottom
        if (scrollRef.current) {
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

        // Add user message immediately
        const userMessage: Message = {
            id: 'temp-' + Date.now(),
            role: 'user',
            content,
            created_at: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setStreaming(true);
        setStreamingContent('');

        try {
            let fullResponse = '';
            let sources: SSEChunk['sources'] = [];
            let assistantMessageId = '';

            for await (const chunk of streamMessage(chat.id, content, token)) {
                if (chunk.type === 'chunk' && chunk.content) {
                    fullResponse += chunk.content;
                    setStreamingContent(fullResponse);
                } else if (chunk.type === 'sources') {
                    sources = chunk.sources;
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
        <div className="flex-1 flex flex-col bg-white dark:bg-gray-800">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold">{chat.title}</h2>
                <p className="text-sm text-gray-500">
                    {chat.mode === 'HYBRID' ? '🌐 Hybrid Mode' : '🔒 Private Mode'}
                </p>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4" ref={scrollRef}>
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
            </ScrollArea>

            {/* Input */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <MessageInput onSend={handleSendMessage} disabled={streaming} />
            </div>
        </div>
    );
}
