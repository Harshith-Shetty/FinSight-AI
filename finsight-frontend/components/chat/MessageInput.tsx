'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';

interface MessageInputProps {
    onSend: (content: string) => void;
    disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
    const [input, setInput] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!input.trim() || disabled) return;

        onSend(input);
        setInput('');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="flex gap-2 max-w-4xl mx-auto w-full">
            <textarea
                aria-label="Message" rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                disabled={disabled}
                className="min-w-0 flex-1 max-h-40 resize-y overflow-y-auto rounded-xl border border-input bg-background px-3 py-2 text-base sm:text-sm focus-visible:outline-2 focus-visible:outline-blue-600"
            />
            <Button aria-label="Send message" className="self-end shrink-0" type="submit" disabled={disabled || !input.trim()}>
                <Send className="h-4 w-4" />
            </Button>
        </form>
    );
}
