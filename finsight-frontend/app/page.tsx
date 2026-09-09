import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowDown, ArrowRight, BookOpen, Check, FileSearch, FileText, Github, Layers, MessageSquare, Sparkles, TrendingUp } from 'lucide-react';
import { LandingActions } from '@/components/LandingActions';

export const metadata: Metadata = {
  title: 'FinSight AI | Turn financial documents into understanding',
  description: 'Explore FinSight AI: upload financial documents, ask questions in plain English, and analyze SEC filings with retrieval-augmented AI. See the product and the engineering behind it.',
};

const features = [
  { icon: FileText, title: 'Bring your documents', description: 'Upload financial reports in PDF, DOCX, TXT, or Markdown. Keep your research together in a searchable document library.', label: 'DOCUMENT LIBRARY' },
  { icon: MessageSquare, title: 'Ask the next question', description: 'Chat with your documents in plain English. Semantic search finds relevant context to help the AI answer your questions.', label: 'CONTEXTUAL CHAT' },
  { icon: TrendingUp, title: 'Look deeper into a filing', description: 'Choose a company ticker, filing year, and focus area to explore an SEC filing through summaries, findings, and source excerpts.', label: 'FINANCIAL ANALYSIS' },
];

const steps = [
  { number: '01', title: 'Start with a source', text: 'Upload a report or select a company filing to analyze.' },
  { number: '02', title: 'Choose your question', text: 'Explore business performance, financial risks, or a specific detail.' },
  { number: '03', title: 'Follow the evidence', text: 'Read the response and use the source context to continue your research.' },
];

const linkStyle = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-600';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#f8fafc] font-sans text-slate-900 selection:bg-blue-100">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-lg focus:bg-white focus:p-4 focus:text-blue-700">Skip to content</a>
      <header className="border-b border-slate-200 bg-white">
        <nav aria-label="Main navigation" className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-4 sm:px-8">
          <Link href="/" aria-label="FinSight AI home" className="flex items-center gap-2.5 rounded-md focus-visible:outline-2 focus-visible:outline-blue-600">
            <span className="rounded-lg bg-blue-600 p-2 text-white"><TrendingUp aria-hidden="true" className="size-5" /></span>
            <span className="text-xl font-semibold tracking-tight">FinSight <span className="text-blue-600">AI</span></span>
          </Link>
          <div className="order-3 flex w-full items-center justify-center gap-5 text-sm text-slate-600 md:order-none md:w-auto">
            <a className="rounded hover:text-blue-600 focus-visible:outline-2 focus-visible:outline-blue-600" href="#features">Features</a>
            <a className="rounded hover:text-blue-600 focus-visible:outline-2 focus-visible:outline-blue-600" href="#how-it-works">How it works</a>
            <a className="rounded hover:text-blue-600 focus-visible:outline-2 focus-visible:outline-blue-600" href="#engineering">Under the hood</a>
          </div>
          <LandingActions compact />
        </nav>
      </header>

      <main id="main">
        <section className="mx-auto grid max-w-7xl items-center gap-12 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-[1fr_1.05fr] lg:gap-16">
          <div>
            <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-medium tracking-wide text-blue-700"><Sparkles aria-hidden="true" className="size-3.5" /> FINANCIAL RESEARCH, WITH CONTEXT</p>
            <h1 className="max-w-xl text-5xl leading-[1.08] font-semibold tracking-[-0.045em] sm:text-6xl">Less searching.<br />More <span className="text-blue-600">understanding.</span></h1>
            <p className="mt-6 max-w-lg text-lg leading-relaxed text-slate-600">Turn dense financial documents into a conversation. FinSight AI helps you explore reports, ask better questions, and connect answers to the source.</p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <LandingActions />
              <a href="#product-preview" className={`${linkStyle} border border-slate-300 bg-white hover:bg-slate-100`}>Explore the product <ArrowDown aria-hidden="true" className="size-4" /></a>
            </div>
            <p className="mt-4 text-xs text-slate-500">Just looking around? Explore this page without an account.</p>
          </div>

          <figure id="product-preview" className="scroll-mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-200/60">
            <figcaption className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-slate-50 px-5 py-4 text-xs">
              <span className="flex items-center gap-2 font-semibold"><FileSearch aria-hidden="true" className="size-4 text-blue-600" /> Inside FinSight AI</span>
              <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-slate-500">Illustrative preview</span>
            </figcaption>
            <div className="space-y-5 p-5 sm:p-7">
              <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-3">
                <FileText aria-hidden="true" className="size-8 text-blue-600" />
                <div className="min-w-0 flex-1"><p className="text-sm font-medium">Example company · Annual report</p><p className="mt-0.5 text-xs text-slate-500">Document context</p></div>
                <Check aria-hidden="true" className="size-4 shrink-0 text-emerald-600" />
              </div>
              <div className="ml-6 rounded-xl rounded-tr-sm bg-blue-600 p-4 text-sm leading-relaxed text-white">What are the main risks to this company’s growth?</div>
              <div className="rounded-xl rounded-tl-sm border border-slate-200 bg-slate-50 p-4">
                <p className="mb-3 flex items-center gap-2 text-xs font-semibold text-blue-700"><Sparkles aria-hidden="true" className="size-4" /> FINSIGHT AI</p>
                <p className="text-sm leading-relaxed text-slate-600">The report highlights three areas to investigate:</p>
                <ul className="mt-3 space-y-3 text-sm">
                  {['Demand: changes in customer spending.', 'Margins: rising operating and input costs.', 'Operations: reliance on key suppliers.'].map((item, index) => (
                    <li key={item} className="flex gap-2.5"><span className="flex size-5 shrink-0 items-center justify-center rounded bg-blue-100 text-xs font-semibold text-blue-700">{index + 1}</span><span>{item}</span></li>
                  ))}
                </ul>
                <div className="mt-4 border-t border-slate-200 pt-3 text-xs text-slate-500"><span className="font-medium text-slate-700">Source context</span> · Risk factors · Example excerpt</div>
              </div>
              <p className="text-xs leading-relaxed text-slate-500">Sample content showing the research workflow, not a live analysis.</p>
            </div>
          </figure>
        </section>

        <section id="features" aria-labelledby="features-title" className="scroll-mt-8 border-y border-slate-200 bg-white">
          <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8 sm:py-20">
            <p className="text-xs font-semibold tracking-[0.18em] text-blue-600">FROM DOCUMENTS TO INSIGHTS</p>
            <h2 id="features-title" className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">A clearer way to read between the lines.</h2>
            <div className="mt-10 grid gap-8 md:grid-cols-3">
              {features.map(({ icon: Icon, title, description, label }) => (
                <article key={title} className="border-t border-slate-200 pt-6">
                  <Icon aria-hidden="true" className="mb-6 size-7 text-blue-600" />
                  <p className="text-[10px] font-semibold tracking-[0.15em] text-slate-500">{label}</p>
                  <h3 className="mt-2 text-xl font-semibold tracking-tight">{title}</h3>
                  <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="how-it-works" aria-labelledby="workflow-title" className="mx-auto max-w-7xl scroll-mt-8 px-5 py-16 sm:px-8 sm:py-20">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
            <div><p className="text-xs font-semibold tracking-[0.18em] text-blue-600">THE WORKFLOW</p><h2 id="workflow-title" className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Bring your curiosity.<br />Start with the evidence.</h2><p className="mt-4 text-sm leading-7 text-slate-600">A focused workspace for moving from a long report to a more informed next question.</p></div>
            <ol className="divide-y divide-slate-200">
              {steps.map(({ number, title, text }) => <li key={number} className="flex gap-5 py-5 first:pt-0"><span className="pt-1 font-mono text-sm text-blue-600">{number}</span><div><h3 className="text-lg font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-600">{text}</p></div></li>)}
            </ol>
          </div>
        </section>

        <section id="engineering" aria-labelledby="engineering-title" className="scroll-mt-8 bg-slate-950 text-white">
          <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8 sm:py-20">
            <div className="grid gap-10 lg:grid-cols-2 lg:gap-20">
              <div><p className="flex items-center gap-2 text-xs font-semibold tracking-[0.18em] text-blue-400"><Layers aria-hidden="true" className="size-4" /> UNDER THE HOOD</p><h2 id="engineering-title" className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">A full-stack product.<br />An end-to-end AI pipeline.</h2><p className="mt-5 text-sm leading-7 text-slate-400">FinSight AI combines a Next.js interface with a FastAPI backend and retrieval-augmented generation (RAG). Relevant document passages provide context for the model, while background workers handle ingestion and analysis.</p><a href="https://github.com/Harshith-Shetty/FinSight-AI" target="_blank" rel="noopener noreferrer" className={`${linkStyle} mt-6 border border-slate-700 hover:bg-slate-800 focus-visible:outline-blue-400`}><Github aria-hidden="true" className="size-4" /> Explore the source <span className="sr-only">(opens in a new tab)</span><ArrowRight aria-hidden="true" className="size-4" /></a></div>
              <div className="space-y-6 lg:pt-2">
                {[
                  ['Interface & API', 'Next.js · React · Tailwind CSS · FastAPI', 'A modern web interface backed by an asynchronous Python API.'],
                  ['Retrieval & generation', 'Qdrant · sentence-transformers · Groq / Ollama', 'Vector search connects document context with a configurable language model.'],
                  ['Background processing & storage', 'Celery · Redis · PostgreSQL', 'Queued workloads handle heavy processing, with persistent application data.'],
                ].map(([title, stack, description]) => <div key={title} className="border-l-2 border-blue-500/60 pl-5"><h3 className="text-sm font-semibold">{title}</h3><p className="mt-2 font-mono text-xs leading-6 text-blue-300">{stack}</p><p className="mt-1 text-xs leading-6 text-slate-400">{description}</p></div>)}
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 px-5 py-16 sm:px-8 md:flex-row md:items-center">
          <div><BookOpen aria-hidden="true" className="mb-4 size-6 text-blue-600" /><h2 className="text-3xl font-semibold tracking-tight">Your next insight starts with a question.</h2><p className="mt-3 text-sm text-slate-600">Create an account to start exploring financial documents with FinSight AI.</p></div>
          <LandingActions />
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-8"><p className="font-semibold text-slate-700">FinSight AI</p><p>Financial document research, powered by AI.</p><Link href="/login" className="inline-flex min-h-11 items-center rounded px-2 hover:text-blue-600 focus-visible:outline-2 focus-visible:outline-blue-600">Sign in <ArrowRight aria-hidden="true" className="ml-2 size-3" /></Link></div>
      </footer>
    </div>
  );
}
