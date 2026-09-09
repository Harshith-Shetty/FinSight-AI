'use client';

import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export function LandingActions({ compact = false }: { compact?: boolean }) {
  const { isAuthenticated, loading } = useAuth();
  const signedIn = !loading && isAuthenticated;

  return (
    <Link
      href={signedIn ? '/chat' : compact ? '/login' : '/register'}
      className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-600"
    >
      {signedIn ? 'Open workspace' : compact ? 'Sign in' : 'Get started'}
      <ArrowRight aria-hidden="true" className="size-4" />
    </Link>
  );
}
