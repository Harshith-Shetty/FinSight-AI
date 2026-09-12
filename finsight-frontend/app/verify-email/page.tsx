'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { verifyEmail, resendOTP, getCurrentUser } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Mail, ArrowLeft, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import { Suspense } from 'react';

function VerifyEmailContent() {
    const searchParams = useSearchParams();
    const email = searchParams.get('email') || '';
    const [otp, setOtp] = useState<string[]>(['', '', '', '', '', '']);
    const [loading, setLoading] = useState(false);
    const [resendCooldown, setResendCooldown] = useState(0);
    const [resending, setResending] = useState(false);
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
    const router = useRouter();
    const { login } = useAuth();

    // Start cooldown timer on mount (assuming OTP was just sent)
    useEffect(() => {
        setResendCooldown(60);
    }, []);

    // Countdown timer
    useEffect(() => {
        if (resendCooldown <= 0) return;
        const timer = setInterval(() => {
            setResendCooldown((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
        return () => clearInterval(timer);
    }, [resendCooldown]);

    // Focus first input on mount
    useEffect(() => {
        inputRefs.current[0]?.focus();
    }, []);

    const handleChange = (index: number, value: string) => {
        // Only allow digits
        if (value && !/^\d$/.test(value)) return;

        const newOtp = [...otp];
        newOtp[index] = value;
        setOtp(newOtp);

        // Auto-focus next input
        if (value && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }

        // Auto-submit when all 6 digits are entered
        if (value && index === 5 && newOtp.every((d) => d !== '')) {
            handleSubmit(newOtp.join(''));
        }
    };

    const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Backspace' && !otp[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    const handlePaste = (e: React.ClipboardEvent) => {
        e.preventDefault();
        const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
        if (pastedData.length === 0) return;

        const newOtp = [...otp];
        for (let i = 0; i < pastedData.length; i++) {
            newOtp[i] = pastedData[i];
        }
        setOtp(newOtp);

        // Focus the next empty input or the last one
        const nextEmpty = newOtp.findIndex((d) => d === '');
        inputRefs.current[nextEmpty >= 0 ? nextEmpty : 5]?.focus();

        // Auto-submit if all 6 digits pasted
        if (pastedData.length === 6) {
            handleSubmit(pastedData);
        }
    };

    const handleSubmit = useCallback(async (otpCode?: string) => {
        const code = otpCode || otp.join('');
        if (code.length !== 6) {
            toast.error('Please enter the complete 6-digit code');
            return;
        }

        setLoading(true);
        try {
            const tokenResponse = await verifyEmail(email, code);

            // Fetch user profile for the auth context
            const userProfile = await getCurrentUser(tokenResponse.access_token);
            login(tokenResponse.access_token, userProfile);

            toast.success('Email verified! Welcome to FinSight AI 🎉');
            router.push('/chat');
        } catch (error: any) {
            toast.error(error.message || 'Verification failed');
            // Clear OTP on error
            setOtp(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
        } finally {
            setLoading(false);
        }
    }, [otp, email, login, router]);

    const handleResend = async () => {
        if (resendCooldown > 0 || resending) return;

        setResending(true);
        try {
            await resendOTP(email, 'email_verification');
            toast.success('New verification code sent!');
            setResendCooldown(60);
            // Clear existing OTP
            setOtp(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
        } catch (error: any) {
            toast.error(error.message || 'Failed to resend code');
        } finally {
            setResending(false);
        }
    };

    if (!email) {
        return (
            <div className="flex items-center justify-center min-h-dvh bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
                <Card className="w-full max-w-md">
                    <CardContent className="pt-6 text-center">
                        <p className="text-gray-600 dark:text-gray-400 mb-4">
                            No email provided. Please register first.
                        </p>
                        <Link href="/register">
                            <Button>Go to Register</Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-dvh bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-3 text-center">
                    <div className="mx-auto w-14 h-14 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                        <Mail className="h-7 w-7 text-blue-600 dark:text-blue-400" />
                    </div>
                    <CardTitle className="text-2xl font-bold">Verify Your Email</CardTitle>
                    <CardDescription className="text-base">
                        We sent a 6-digit code to<br />
                        <span className="font-medium text-gray-900 dark:text-gray-100">{email}</span>
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* OTP Input Boxes */}
                    <div className="flex justify-center gap-2 sm:gap-3" onPaste={handlePaste}>
                        {otp.map((digit, index) => (
                            <input
                                key={index}
                                ref={(el) => { inputRefs.current[index] = el; }}
                                type="text"
                                inputMode="numeric"
                                maxLength={1}
                                value={digit}
                                onChange={(e) => handleChange(index, e.target.value)}
                                onKeyDown={(e) => handleKeyDown(index, e)}
                                disabled={loading}
                                className="min-w-0 w-full max-w-11 h-12 sm:max-w-13 sm:h-14 text-center text-xl sm:text-2xl font-bold rounded-xl
                                    border-2 border-gray-200 dark:border-gray-700
                                    bg-white dark:bg-gray-800
                                    text-gray-900 dark:text-white
                                    focus:border-blue-500 dark:focus:border-blue-400
                                    focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20
                                    outline-none transition-all duration-200
                                    disabled:opacity-50 disabled:cursor-not-allowed"
                                style={{ width: '2.75rem', height: '3.25rem' }}
                                aria-label={`Digit ${index + 1}`}
                            />
                        ))}
                    </div>

                    {/* Verify Button */}
                    <Button
                        onClick={() => handleSubmit()}
                        className="w-full"
                        disabled={loading || otp.some((d) => d === '')}
                    >
                        {loading ? 'Verifying...' : 'Verify Email'}
                    </Button>

                    {/* Resend Section */}
                    <div className="text-center space-y-2">
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Didn&apos;t receive the code?
                        </p>
                        <button
                            onClick={handleResend}
                            disabled={resendCooldown > 0 || resending}
                            className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                            <RefreshCw className={`h-3.5 w-3.5 ${resending ? 'animate-spin' : ''}`} />
                            {resendCooldown > 0
                                ? `Resend in ${resendCooldown}s`
                                : resending
                                    ? 'Sending...'
                                    : 'Resend Code'
                            }
                        </button>
                    </div>

                    {/* Back to Register */}
                    <div className="text-center pt-2">
                        <Link
                            href="/register"
                            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
                        >
                            <ArrowLeft className="h-3.5 w-3.5" />
                            Back to Register
                        </Link>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

export default function VerifyEmailPage() {
    return (
        <Suspense fallback={
            <div className="flex items-center justify-center min-h-dvh bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
                <div className="text-gray-500">Loading...</div>
            </div>
        }>
            <VerifyEmailContent />
        </Suspense>
    );
}
