'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useRef } from 'react';
import { ArrowLeft, Search, Loader2, TrendingUp, AlertTriangle, FileText, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { submitAnalysis, getTaskStatus } from '@/lib/api';

const YEARS = [2026, 2025, 2024, 2023];
const FOCUS_AREAS = [
    { value: 'balance_sheet', label: 'Balance Sheet Analysis' },
    { value: 'cash_flow', label: 'Cash Flow Analysis' },
    { value: 'income_statement', label: 'Income Statement Analysis' },
    { value: 'risk_factors', label: 'Item 1A Risk Factors' },
    { value: 'material_weaknesses', label: 'SOX Internal Controls & Weaknesses' }
];

export default function TickerAnalysisPage() {
    const { isAuthenticated, loading, token } = useAuth();
    const router = useRouter();

    const [ticker, setTicker] = useState('');
    const [filingYear, setFilingYear] = useState(2024);
    const [focusArea, setFocusArea] = useState('balance_sheet');
    const [submitting, setSubmitting] = useState(false);
    
    // Polling states
    const [taskId, setTaskId] = useState<string | null>(null);
    const [taskStatus, setTaskStatus] = useState<'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | null>(null);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    
    // Multi-phase loader simulated milestones
    const [loaderPhase, setLoaderPhase] = useState('Queuing background worker...');

    const pollingRef = useRef<NodeJS.Timeout | null>(null);

    // Protection
    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, loading, router]);

    // Handle Polling Clean Up
    useEffect(() => {
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
        };
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!isAuthenticated) return null;

    const startPolling = (tid: string) => {
        if (!token) return;
        setTaskId(tid);
        setTaskStatus('PENDING');
        setSubmitting(true);
        setResult(null);
        setError(null);

        let counter = 0;
        pollingRef.current = setInterval(async () => {
            try {
                counter++;
                const statusRes = await getTaskStatus(tid, token);
                setTaskStatus(statusRes.status);
                
                // Advance loader phases dynamically for awesome aesthetic progress feedback
                if (statusRes.status === 'PENDING') {
                    setLoaderPhase('Queuing financial analyzer task...');
                } else if (statusRes.status === 'PROCESSING') {
                    if (counter < 4) setLoaderPhase('Downloading target SEC filing filings...');
                    else if (counter < 8) setLoaderPhase('Applying RAG embedding similarity searches...');
                    else setLoaderPhase('Synthesizing expert financial LLM conclusions...');
                }

                if (statusRes.status === 'COMPLETED') {
                    setResult(statusRes.result);
                    setSubmitting(false);
                    toast.success('Financial analysis complete!');
                    if (pollingRef.current) clearInterval(pollingRef.current);
                } else if (statusRes.status === 'FAILED') {
                    setError(statusRes.error || 'Ingestion analysis run crashed.');
                    setSubmitting(false);
                    toast.error('Financial analysis failed');
                    if (pollingRef.current) clearInterval(pollingRef.current);
                }
            } catch (err: any) {
                console.error(err);
                setError(err.message || 'Polling error encountered.');
                setSubmitting(false);
                if (pollingRef.current) clearInterval(pollingRef.current);
            }
        }, 2000);
    };

    const handleFormSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!ticker || !token) return;

        try {
            setSubmitting(true);
            setResult(null);
            setError(null);
            setTaskId(null);
            setTaskStatus(null);
            setLoaderPhase('Submitting request to FinSight AI cluster...');

            const res = await submitAnalysis(ticker.toUpperCase().trim(), focusArea, filingYear, token);
            startPolling(res.task_id);
        } catch (err: any) {
            toast.error(err.message || 'Submission failed');
            setSubmitting(false);
        }
    };

    // Helper to render sentiment color code
    const getSentimentBadge = (sentiment: string) => {
        const lower = (sentiment || '').toLowerCase();
        if (lower.includes('bullish') || lower.includes('positive') || lower.includes('strong')) {
            return <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider shadow-[0_0_15px_rgba(16,185,129,0.1)]">Bullish</span>;
        } else if (lower.includes('bearish') || lower.includes('negative') || lower.includes('weak')) {
            return <span className="bg-rose-500/10 text-rose-500 border border-rose-500/20 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider shadow-[0_0_15px_rgba(244,63,94,0.1)]">Bearish</span>;
        }
        return <span className="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider shadow-[0_0_15px_rgba(245,158,11,0.1)]">Neutral</span>;
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-6 md:p-12 text-gray-900 dark:text-gray-100 transition-colors duration-200">
            <div className="max-w-6xl mx-auto space-y-8">
                
                {/* Header */}
                <div className="flex items-center space-x-4">
                    <Button variant="ghost" size="icon" onClick={() => router.push('/chat')} className="hover:bg-gray-100 dark:hover:bg-gray-800">
                        <ArrowLeft className="h-6 w-6" />
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent dark:from-blue-400 dark:to-indigo-400">Deep Ticker Analysis</h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Deploy RAG and Financial LLM pipelines on raw SEC filings.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                    
                    {/* Control Panel Card */}
                    <Card className="lg:col-span-1 p-6 border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_30px_rgba(0,0,0,0.15)] rounded-2xl backdrop-blur-md">
                        <h3 className="text-lg font-semibold mb-4 border-b border-gray-100 dark:border-gray-800 pb-2">Analysis Targets</h3>
                        <form onSubmit={handleFormSubmit} className="space-y-5">
                            <div>
                                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Ticker Symbol</label>
                                <div className="relative">
                                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                                    <input 
                                        type="text" 
                                        placeholder="e.g. AAPL, MSFT, TSLA"
                                        value={ticker}
                                        onChange={(e) => setTicker(e.target.value)}
                                        disabled={submitting}
                                        required
                                        className="pl-10 w-full p-2 text-sm border rounded-xl bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600 focus:border-transparent transition-all font-mono"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Filing Year</label>
                                    <select
                                        value={filingYear}
                                        onChange={(e) => setFilingYear(Number(e.target.value))}
                                        disabled={submitting}
                                        className="w-full p-2 text-sm border rounded-xl bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Platform Engine</label>
                                    <select
                                        disabled
                                        className="w-full p-2 text-sm border rounded-xl bg-gray-100 dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-400"
                                    >
                                        <option>Hybrid RAG + Groq</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Focus Focus Area</label>
                                <select
                                    value={focusArea}
                                    onChange={(e) => setFocusArea(e.target.value)}
                                    disabled={submitting}
                                    className="w-full p-2 text-sm border rounded-xl bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {FOCUS_AREAS.map(fa => <option key={fa.value} value={fa.value}>{fa.label}</option>)}
                                </select>
                            </div>

                            <Button 
                                type="submit" 
                                disabled={submitting || !ticker}
                                className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium shadow-md hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg disabled:opacity-50 transition-all duration-200 flex items-center justify-center gap-2"
                            >
                                {submitting ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Analyzing...
                                    </>
                                ) : (
                                    'Analyze Ticker'
                                )}
                            </Button>
                        </form>
                    </Card>

                    {/* Results / Progress Console */}
                    <div className="lg:col-span-2 space-y-6">
                        
                        {/* Submitting & Progress State */}
                        {submitting && (
                            <Card className="p-8 flex flex-col items-center justify-center space-y-6 border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900/60 rounded-2xl min-h-[300px] shadow-sm">
                                <div className="relative flex items-center justify-center">
                                    <div className="animate-ping absolute inline-flex h-16 w-16 rounded-full bg-blue-400 opacity-20"></div>
                                    <div className="relative rounded-full p-4 bg-blue-50 dark:bg-blue-900/40">
                                        <Loader2 className="h-10 w-10 text-blue-600 animate-spin" />
                                    </div>
                                </div>
                                <div className="text-center space-y-2 max-w-sm">
                                    <h4 className="font-semibold text-lg uppercase tracking-wide text-blue-600 dark:text-blue-400">{taskStatus || 'INITIATING'}</h4>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 font-medium animate-pulse">{loaderPhase}</p>
                                    <p className="text-xs text-gray-400 font-mono">Task ID: {taskId || 'Waiting for slot...'}</p>
                                </div>
                            </Card>
                        )}

                        {/* Error State */}
                        {error && (
                            <Card className="p-6 border-rose-500/20 bg-rose-50 dark:bg-rose-950/20 text-rose-800 dark:text-rose-400 rounded-2xl flex items-start gap-4">
                                <AlertTriangle className="h-6 w-6 text-rose-500 shrink-0 mt-0.5" />
                                <div>
                                    <h4 className="font-bold mb-1">Analysis Error Encountered</h4>
                                    <p className="text-sm font-mono bg-white/40 dark:bg-black/20 p-3 rounded-lg border border-rose-500/10 mt-2">{error}</p>
                                </div>
                            </Card>
                        )}

                        {/* Initial Placeholder State */}
                        {!submitting && !result && !error && (
                            <Card className="p-12 flex flex-col items-center justify-center text-center space-y-4 border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 rounded-2xl min-h-[350px] shadow-sm">
                                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-full text-gray-400">
                                    <TrendingUp className="h-12 w-12" />
                                </div>
                                <div className="space-y-2 max-w-sm">
                                    <h3 className="text-xl font-bold">Awaiting Analysis Targets</h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Enter a stock ticker and select a focus area to trigger our deep financial intelligence analysis run.</p>
                                </div>
                            </Card>
                        )}

                        {/* Success Display Analysis Results */}
                        {result && (
                            <div className="space-y-6 animate-in fade-in duration-300">
                                
                                {/* Top Summary Card */}
                                <Card className="p-6 border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 rounded-2xl shadow-sm space-y-6">
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 dark:border-gray-800 pb-4">
                                        <div>
                                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                                {result.ticker || ticker.toUpperCase()}
                                                <span className="text-sm font-normal text-gray-400">({result.filing_year || filingYear} Annual Report)</span>
                                            </h2>
                                            <p className="text-xs text-gray-500 mt-1">Processed: {result.analysis_date || new Date().toLocaleDateString()}</p>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm text-gray-400">Sentiment Outcome:</span>
                                            {getSentimentBadge(result.sentiment || 'Neutral')}
                                        </div>
                                    </div>

                                    {/* Executive Summary */}
                                    <div>
                                        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Executive Summary</h4>
                                        <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-line bg-gray-50 dark:bg-gray-950 p-4 rounded-xl border border-gray-100 dark:border-gray-800">
                                            {result.analysis || result.summary}
                                        </p>
                                    </div>
                                </Card>

                                {/* Key Findings & Core Risks */}
                                {result.key_findings && (
                                    <Card className="p-6 border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 rounded-2xl shadow-sm space-y-4">
                                        <h3 className="font-semibold text-lg flex items-center gap-2 border-b border-gray-100 dark:border-gray-800 pb-2">
                                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                                            Key Findings & Risks
                                        </h3>
                                        <div className="space-y-3">
                                            {Array.isArray(result.key_findings) ? (
                                                result.key_findings.map((item: string, idx: number) => (
                                                    <div key={idx} className="flex gap-3 items-start p-3 bg-amber-500/5 hover:bg-amber-500/10 rounded-xl transition-all border border-amber-500/10">
                                                        <ChevronRight className="h-4 w-4 text-amber-500 mt-1 shrink-0" />
                                                        <span className="text-sm text-gray-700 dark:text-gray-300">{item}</span>
                                                    </div>
                                                ))
                                            ) : (
                                                <p className="text-sm text-gray-700 dark:text-gray-300">{result.key_findings}</p>
                                            )}
                                        </div>
                                    </Card>
                                )}

                                {/* Citations Drawer */}
                                {result.citations && result.citations.length > 0 && (
                                    <Card className="p-6 border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 rounded-2xl shadow-sm space-y-4">
                                        <h3 className="font-semibold text-lg flex items-center gap-2 border-b border-gray-100 dark:border-gray-800 pb-2">
                                            <FileText className="h-5 w-5 text-blue-500" />
                                            Citations & Excerpt References
                                        </h3>
                                        <div className="grid grid-cols-1 gap-4">
                                            {result.citations.map((cite: any, idx: number) => (
                                                <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-xl space-y-2">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-xs font-mono font-semibold bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 px-2 py-0.5 rounded-full">Source Citation {idx + 1}</span>
                                                        {cite.score && (
                                                            <span className="text-xs text-gray-400 font-mono">Similarity: {Math.round(cite.score * 100)}%</span>
                                                        )}
                                                    </div>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400 italic">"{cite.text || cite}"</p>
                                                </div>
                                            ))}
                                        </div>
                                    </Card>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
