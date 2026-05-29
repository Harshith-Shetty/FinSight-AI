'use client';

import { Message } from '@/types';
import { User, Bot } from 'lucide-react';

interface MessageBubbleProps {
    message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`
          flex gap-3 max-w-[80%]
          ${isUser ? 'flex-row-reverse' : 'flex-row'}
        `}
            >
                {/* Avatar */}
                <div
                    className={`
            flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
            ${isUser ? 'bg-blue-500' : 'bg-gray-700'}
          `}
                >
                    {isUser ? (
                        <User className="h-5 w-5 text-white" />
                    ) : (
                        <Bot className="h-5 w-5 text-white" />
                    )}
                </div>

                {/* Message Content */}
                <div
                    className={`
            rounded-lg px-4 py-2
            ${isUser
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                        }
          `}
                >
                    <p className="whitespace-pre-wrap break-words">{message.content}</p>

                    {/* Sources */}
                    {message.metadata?.sources && message.metadata.sources.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-gray-300 dark:border-gray-600">
                            <p className="text-xs font-semibold mb-1">Sources:</p>
                            <div className="space-y-1">
                                {message.metadata.sources.map((source, idx) => (
                                    <div key={idx} className="text-xs opacity-80">
                                        <span className="font-medium">
                                            {source.source === 'user' ? '📄' : '🌐'}
                                        </span>
                                        {' '}
                                        Score: {(source.score * 100).toFixed(1)}%
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
