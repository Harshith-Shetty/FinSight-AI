'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { forgotPassword, resetPassword, resendOTP } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { KeyRound, ArrowLeft, RefreshCw, Eye, EyeOff, CheckCircle2 } from 'lucide-react';

type Step = 'email' | 'otp' | 'success';

export default function ForgotPasswordPage() {
    const [step, setStep] = useState<Step>('email');
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState<string[]>(['', '', '', '', '', '']);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [resendCooldown, setResendCooldown] = useState(0);
    const [resending, setResending] = useState(false);
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
    const router = useRouter();

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

    // Focus first OTP input when entering OTP step
    useEffect(() => {
        if (step === 'otp') {
            inputRefs.current[0]?.focus();
        }
    }, [step]);

    // ─── Step 1: Email submission ────────────────────────────────
    const handleEmailSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            await forgotPassword(email);
            toast.success('Reset code sent! Check your email.');
            setStep('otp');
            setResendCooldown(60);
        } catch (error: any) {
            toast.error(error.message || 'Failed to send reset code');
        } finally {
            setLoading(false);
        }
    };

    // ─── Step 2: OTP + New Password ──────────────────────────────
    const handleOtpChange = (index: number, value: string) => {
        if (value && !/^\d$/.test(value)) return;

        const newOtp = [...otp];
        newOtp[index] = value;
        setOtp(newOtp);

        if (value && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }
    };

    const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Backspace' && !otp[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    const handleOtpPaste = (e: React.ClipboardEvent) => {
        e.preventDefault();
        const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
        if (pastedData.length === 0) return;

        const newOtp = [...otp];
        for (let i = 0; i < pastedData.length; i++) {
            newOtp[i] = pastedData[i];
        }
        setOtp(newOtp);

        const nextEmpty = newOtp.findIndex((d) => d === '');
        inputRefs.current[nextEmpty >= 0 ? nextEmpty : 5]?.focus();
    };

    const handleResetSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const code = otp.join('');
        if (code.length !== 6) {
            toast.error('Please enter the complete 6-digit code');
            return;
        }

        if (newPassword.length < 8) {
            toast.error('Password must be at least 8 characters');
            return;
        }

        if (newPassword !== confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }

        setLoading(true);
        try {
            await resetPassword(email, code, newPassword);
            toast.success('Password reset successfully!');
            setStep('success');
        } catch (error: any) {
            toast.error(error.message || 'Failed to reset password');
            // Clear OTP on error
            setOtp(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
        } finally {
            setLoading(false);
        }
    };

    const handleResend = async () => {
        if (resendCooldown > 0 || resending) return;

        setResending(true);
        try {
            await resendOTP(email, 'password_reset');
            toast.success('New reset code sent!');
            setResendCooldown(60);
            setOtp(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
        } catch (error: any) {
            toast.error(error.message || 'Failed to resend code');
        } finally {
            setResending(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
            <Card className="w-full max-w-md">
                {/* ─── Step 1: Enter Email ─────────────────────────────────── */}
                {step === 'email' && (
                    <>
                        <CardHeader className="space-y-3 text-center">
                            <div className="mx-auto w-14 h-14 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
                                <KeyRound className="h-7 w-7 text-orange-600 dark:text-orange-400" />
                            </div>
                            <CardTitle className="text-2xl font-bold">Forgot Password?</CardTitle>
                            <CardDescription className="text-base">
                                No worries! Enter your email and we&apos;ll send you a reset code.
                            </CardDescription>
                        </CardHeader>
                        <form onSubmit={handleEmailSubmit}>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <label htmlFor="fp-email" className="text-sm font-medium">
                                        Email Address
                                    </label>
                                    <Input
                                        id="fp-email"
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        disabled={loading}
                                    />
                                </div>
                                <Button type="submit" className="w-full" disabled={loading}>
                                    {loading ? 'Sending...' : 'Send Reset Code'}
                                </Button>
                                <div className="text-center pt-2">
                                    <Link
                                        href="/login"
                                        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
                                    >
                                        <ArrowLeft className="h-3.5 w-3.5" />
                                        Back to Login
                                    </Link>
                                </div>
                            </CardContent>
                        </form>
                    </>
                )}

                {/* ─── Step 2: Enter OTP + New Password ───────────────────── */}
                {step === 'otp' && (
                    <>
                        <CardHeader className="space-y-3 text-center">
                            <div className="mx-auto w-14 h-14 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
                                <KeyRound className="h-7 w-7 text-orange-600 dark:text-orange-400" />
                            </div>
                            <CardTitle className="text-2xl font-bold">Reset Password</CardTitle>
                            <CardDescription className="text-base">
                                Enter the code sent to<br />
                                <span className="font-medium text-gray-900 dark:text-gray-100">{email}</span>
                            </CardDescription>
                        </CardHeader>
                        <form onSubmit={handleResetSubmit}>
                            <CardContent className="space-y-5">
                                {/* OTP Input Boxes */}
                                <div className="flex justify-center gap-2 sm:gap-3" onPaste={handleOtpPaste}>
                                    {otp.map((digit, index) => (
                                        <input
                                            key={index}
                                            ref={(el) => { inputRefs.current[index] = el; }}
                                            type="text"
                                            inputMode="numeric"
                                            maxLength={1}
                                            value={digit}
                                            onChange={(e) => handleOtpChange(index, e.target.value)}
                                            onKeyDown={(e) => handleOtpKeyDown(index, e)}
                                            disabled={loading}
                                            className="w-11 h-13 sm:w-13 sm:h-15 text-center text-xl sm:text-2xl font-bold rounded-xl
                                                border-2 border-gray-200 dark:border-gray-700
                                                bg-white dark:bg-gray-800
                                                text-gray-900 dark:text-white
                                                focus:border-orange-500 dark:focus:border-orange-400
                                                focus:ring-2 focus:ring-orange-500/20 dark:focus:ring-orange-400/20
                                                outline-none transition-all duration-200
                                                disabled:opacity-50 disabled:cursor-not-allowed"
                                            style={{ width: '2.75rem', height: '3.25rem' }}
                                            aria-label={`Digit ${index + 1}`}
                                        />
                                    ))}
                                </div>

                                {/* Resend */}
                                <div className="text-center">
                                    <button
                                        type="button"
                                        onClick={handleResend}
                                        disabled={resendCooldown > 0 || resending}
                                        className="inline-flex items-center gap-1.5 text-sm font-medium text-orange-600 hover:text-orange-700 dark:text-orange-400 dark:hover:text-orange-300 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
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

                                {/* New Password */}
                                <div className="space-y-2">
                                    <label htmlFor="new-password" className="text-sm font-medium">
                                        New Password
                                    </label>
                                    <div className="relative">
                                        <Input
                                            id="new-password"
                                            type={showPassword ? "text" : "password"}
                                            placeholder="Enter new password"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            required
                                            disabled={loading}
                                            className="pr-10"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                        >
                                            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                        </button>
                                    </div>
                                </div>

                                {/* Confirm Password */}
                                <div className="space-y-2">
                                    <label htmlFor="confirm-new-password" className="text-sm font-medium">
                                        Confirm New Password
                                    </label>
                                    <div className="relative">
                                        <Input
                                            id="confirm-new-password"
                                            type={showConfirmPassword ? "text" : "password"}
                                            placeholder="Confirm new password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            required
                                            disabled={loading}
                                            className="pr-10"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                        >
                                            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                        </button>
                                    </div>
                                </div>

                                <Button
                                    type="submit"
                                    className="w-full"
                                    disabled={loading || otp.some((d) => d === '')}
                                >
                                    {loading ? 'Resetting...' : 'Reset Password'}
                                </Button>

                                <div className="text-center">
                                    <button
                                        type="button"
                                        onClick={() => setStep('email')}
                                        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
                                    >
                                        <ArrowLeft className="h-3.5 w-3.5" />
                                        Use a different email
                                    </button>
                                </div>
                            </CardContent>
                        </form>
                    </>
                )}

                {/* ─── Step 3: Success ─────────────────────────────────────── */}
                {step === 'success' && (
                    <>
                        <CardHeader className="space-y-3 text-center">
                            <div className="mx-auto w-14 h-14 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                <CheckCircle2 className="h-7 w-7 text-green-600 dark:text-green-400" />
                            </div>
                            <CardTitle className="text-2xl font-bold">Password Reset!</CardTitle>
                            <CardDescription className="text-base">
                                Your password has been updated successfully. You can now sign in with your new password.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button
                                className="w-full"
                                onClick={() => router.push('/login')}
                            >
                                Go to Login
                            </Button>
                        </CardContent>
                    </>
                )}
            </Card>
        </div>
    );
}
