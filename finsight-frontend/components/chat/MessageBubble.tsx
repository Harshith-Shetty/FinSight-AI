'use client';

import { Fragment, useId } from 'react';
import { Message, Source } from '@/types';
import { User, Bot, FileText } from 'lucide-react';

function sourceName(source: Source, index: number): string {
    const name = source.filename || source.metadata?.filename;
    return typeof name === 'string' && name !== 'unknown'
        ? name
        : source.document_id ? `Document ${source.document_id}` : `Source ${index + 1}`;
}

export function MessageBubble({ message }: { message: Message }) {
    const isUser = message.role === 'user';
    const prefix = useId();
    const sources = message.metadata?.sources ?? [];

    function inline(text: string) {
        return text.split(/(\[\d+\]|\*\*[^*]+\*\*|`[^`]+`)/g).map((part, i) => {
            const citation = part.match(/^\[(\d+)\]$/);
            if (citation && sources[Number(citation[1]) - 1]) {
                const number = Number(citation[1]);
                return <button key={i} type="button" className="mx-0.5 rounded bg-blue-100 px-1 text-xs font-semibold text-blue-800 underline-offset-2 hover:underline focus-visible:outline-2 dark:bg-blue-900 dark:text-blue-100"
                    aria-label={`Read source ${number}: ${sourceName(sources[number - 1], number - 1)}`}
                    onClick={() => {
                        const target = document.getElementById(`${prefix}-source-${number}`) as HTMLDetailsElement | null;
                        if (target) { target.open = true; target.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); target.querySelector('summary')?.focus(); }
                    }}>{part}</button>;
            }
            if (part.startsWith('**') && part.endsWith('**')) return <strong key={i}>{part.slice(2, -2)}</strong>;
            if (part.startsWith('`') && part.endsWith('`')) return <code key={i} className="rounded bg-black/5 px-1 font-mono text-[0.9em] dark:bg-white/10">{part.slice(1, -1)}</code>;
            return <Fragment key={i}>{part}</Fragment>;
        });
    }

    function answer() {
        return message.content.split(/(```[\s\S]*?```)/g).map((section, index) => {
            if (section.startsWith('```')) {
                return <pre key={index} className="my-3 max-w-full overflow-x-auto rounded-lg bg-gray-900 p-3 text-sm text-gray-100"><code>{section.slice(3, -3).replace(/^\w*\n/, '')}</code></pre>;
            }
            const lines = section.split('\n');
            const tableRows = new Set<number>();
            return <div key={index} className="space-y-2">{lines.map((line, row) => {
                if (tableRows.has(row)) return null;
                if (line.includes('|') && /^\s*\|?\s*:?-{3,}/.test(lines[row + 1] ?? '')) {
                    const cells = (value: string) => value.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());
                    const rows: string[][] = [];
                    tableRows.add(row + 1);
                    for (let cursor = row + 2; cursor < lines.length && lines[cursor].includes('|'); cursor++) {
                        rows.push(cells(lines[cursor])); tableRows.add(cursor);
                    }
                    return <div key={row} className="max-w-full overflow-x-auto rounded-lg border border-gray-300 dark:border-gray-700" tabIndex={0} aria-label="Answer table"><table className="w-full text-left text-sm"><thead><tr>{cells(line).map((cell, i) => <th scope="col" key={i} className="border-b p-2 font-semibold">{inline(cell)}</th>)}</tr></thead><tbody>{rows.map((cells, i) => <tr key={i}>{cells.map((cell, j) => <td key={j} className="border-b p-2 align-top">{inline(cell)}</td>)}</tr>)}</tbody></table></div>;
                }
                if (!line.trim()) return <div key={row} className="h-1" />;
                const heading = line.match(/^#{1,6}\s+(.+)/);
                if (heading) return <p key={row} className="pt-2 font-semibold">{inline(heading[1])}</p>;
                const bullet = line.match(/^\s*(?:[-*]|(\d+)\.)\s+(.+)/);
                if (bullet) return <div key={row} className="flex gap-2 pl-2"><span className="shrink-0">{bullet[1] ? `${bullet[1]}.` : '•'}</span><div className="min-w-0">{inline(bullet[2])}</div></div>;
                return <p key={row}>{inline(line)}</p>;
            })}</div>;
        });
    }

    return (
        <article className={`flex ${isUser ? 'justify-end' : 'justify-start'}`} aria-label={isUser ? 'Your message' : 'FinSight AI answer'}>
            <div className={`flex min-w-0 gap-2 sm:gap-3 ${isUser ? 'max-w-[92%] flex-row-reverse' : 'w-full'}`}>
                <div className={`hidden size-8 shrink-0 items-center justify-center rounded-full sm:flex ${isUser ? 'bg-blue-600' : 'bg-gray-700'}`}>
                    {isUser ? <User aria-hidden="true" className="size-4 text-white" /> : <Bot aria-hidden="true" className="size-4 text-white" />}
                </div>
                <div className={`min-w-0 max-w-full rounded-2xl px-4 py-3 text-sm leading-7 [overflow-wrap:anywhere] ${isUser ? 'bg-blue-600 text-white' : 'flex-1 border border-gray-200 bg-gray-50 text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100'}`}>
                    {isUser ? <p className="whitespace-pre-wrap">{message.content}</p> : answer()}
                    {!isUser && sources.length > 0 && (
                        <section className="mt-5 space-y-2 border-t border-gray-200 pt-3 dark:border-gray-700" aria-label="Document sources">
                            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Document sources · {sources.length}</p>
                            {sources.map((source, index) => (
                                <details id={`${prefix}-source-${index + 1}`} key={index} className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
                                    <summary className="cursor-pointer rounded text-sm font-medium focus-visible:outline-2 focus-visible:outline-blue-600">
                                        <span className="mr-2 text-blue-600 dark:text-blue-300">[{index + 1}]</span>
                                        <FileText aria-hidden="true" className="mr-1 inline size-4" />
                                        {sourceName(source, index)}
                                    </summary>
                                    <p className="mt-2 text-xs text-gray-500">{source.source === 'user' ? 'Your uploaded document' : 'System knowledge base'}</p>
                                    <blockquote className="mt-2 max-h-64 overflow-y-auto overscroll-contain whitespace-pre-wrap border-l-2 border-blue-400 pl-3 text-sm text-gray-600 dark:text-gray-300" tabIndex={0} aria-label={`Source ${index + 1} excerpt`}>
                                        {source.text || 'No excerpt is available for this saved source.'}
                                    </blockquote>
                                </details>
                            ))}
                        </section>
                    )}
                </div>
            </div>
        </article>
    );
}