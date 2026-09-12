'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getChats, createChat } from '@/lib/api';
import { Chat } from '@/types';
import { ChatSidebar } from '@/components/chat/ChatSidebar';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { Button } from '@/components/ui/button';
import { PlusCircle, Menu } from 'lucide-react';
import { toast } from 'sonner';

export default function ChatPage() {
    const { token } = useAuth();
    const [chats, setChats] = useState<Chat[]>([]);
    const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
    const [loading, setLoading] = useState(true);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    useEffect(() => {
        loadChats();
    }, []);

    const loadChats = async () => {
        if (!token) return;

        try {
            const data = await getChats(token);
            setChats(data);
            
            // Sync selectedChat to reflect title updates
            if (selectedChat) {
                const updated = data.find(c => c.id === selectedChat.id);
                setSelectedChat(updated ?? data[0] ?? null);
            } else if (data.length > 0) {
                setSelectedChat(data[0]);
            }
        } catch (error: any) {
            toast.error('Failed to load chats');
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = async (mode: 'HYBRID' | 'PRIVATE') => {
        console.log('handleNewChat called with mode:', mode);
        console.log('Current token:', token ? 'exists' : 'missing');

        if (!token) {
            console.error('No token available');
            toast.error('Authentication required');
            return;
        }

        try {
            console.log('Calling createChat API...');
            const newChat = await createChat({ mode }, token);
            console.log('New chat created:', newChat);

            setChats([newChat, ...chats]);
            setSelectedChat(newChat);
            toast.success('New chat created');
        } catch (error: any) {
            console.error('Error creating chat:', error);
            toast.error(error.message || 'Failed to create chat');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-dvh">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    return (
        <div className="flex h-dvh overflow-hidden bg-gray-50 dark:bg-gray-900">
            {/* Sidebar */}
            <ChatSidebar
                chats={chats}
                selectedChat={selectedChat}
                onSelectChat={setSelectedChat}
                onNewChat={handleNewChat}
                onDeleteChat={loadChats}
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
            />

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col min-h-0 min-w-0">
                {selectedChat ? (
                    <ChatWindow
                        key={selectedChat.id}
                        chat={selectedChat}
                        onMessageSent={loadChats}
                        onOpenSidebar={() => setSidebarOpen(true)}
                    />
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-500 px-4 text-center">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="md:hidden absolute top-4 left-4"
                            onClick={() => setSidebarOpen(true)}
                        >
                            <Menu className="h-5 w-5" />
                        </Button>
                        <h2 className="text-2xl font-semibold mb-4">Welcome to FinSight AI</h2>
                        <p className="mb-6">Select a chat or create a new one to get started</p>
                        <div className="flex flex-col sm:flex-row gap-4">
                            <Button onClick={() => handleNewChat('HYBRID')}>
                                <PlusCircle className="mr-2 h-4 w-4" />
                                New Hybrid Chat
                            </Button>
                            <Button onClick={() => handleNewChat('PRIVATE')} variant="outline">
                                <PlusCircle className="mr-2 h-4 w-4" />
                                New Private Chat
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
