'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { User, Shield, CreditCard, Clock, CheckCircle2, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { getMyProfile, requestPlanUpgrade } from '@/lib/api';

export default function ProfilePage() {
    const { isAuthenticated, loading, user, token } = useAuth();
    const router = useRouter();

    const [profileData, setProfileData] = useState<any>(null);
    const [fetching, setFetching] = useState(true);
    const [upgradeReason, setUpgradeReason] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [showUpgradeModal, setShowUpgradeModal] = useState(false);

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push('/login');
        } else if (isAuthenticated && token) {
            fetchProfile();
        }
    }, [isAuthenticated, loading, router, token]);

    const fetchProfile = async () => {
        try {
            const data = await getMyProfile(token!);
            setProfileData(data);
        } catch (error: any) {
            toast.error(error.message || 'Failed to fetch profile');
        } finally {
            setFetching(false);
        }
    };

    const handleUpgradeRequest = async () => {
        if (upgradeReason.length < 10) {
            toast.error('Please provide a reason with at least 10 characters.');
            return;
        }
        setSubmitting(true);
        try {
            await requestPlanUpgrade(upgradeReason, token!);
            toast.success('Upgrade request submitted successfully!');
            setShowUpgradeModal(false);
            setUpgradeReason('');
            fetchProfile(); // Refresh profile state
        } catch (error: any) {
            toast.error(error.message || 'Failed to request upgrade');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading || fetching) {
        return (
            <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!profileData || !user) return null;

    const isPremium = user.role.toLowerCase() === 'premium' || user.role.toLowerCase() === 'admin';
    const isPending = profileData.has_pending_upgrade_request;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                <div className="flex items-center space-x-4 mb-8">
                    <Button variant="ghost" size="icon" onClick={() => router.push('/chat')}>
                        <ArrowLeft className="h-6 w-6" />
                    </Button>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <User className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                        My Profile
                    </h1>
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* User Info Card */}
                    <Card className="p-6">
                        <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                            <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                            Account Details
                        </h2>
                        
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm text-gray-500 dark:text-gray-400 block mb-1">Email Address</label>
                                <div className="font-medium bg-gray-100 dark:bg-gray-800 p-3 rounded-md border border-gray-200 dark:border-gray-700">
                                    {profileData.user.email}
                                </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-gray-500 dark:text-gray-400 block mb-1">Current Plan</label>
                                    <div className="flex items-center gap-2 font-medium bg-gray-100 dark:bg-gray-800 p-3 rounded-md border border-gray-200 dark:border-gray-700 capitalize">
                                        {profileData.user.role.toLowerCase()}
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm text-gray-500 dark:text-gray-400 block mb-1">Tokens Used (This Month)</label>
                                    <div className="font-medium bg-gray-100 dark:bg-gray-800 p-3 rounded-md border border-gray-200 dark:border-gray-700">
                                        {profileData.tokens_used_this_month}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Card>

                    {/* Subscription Card */}
                    <Card className="p-6 relative overflow-hidden">
                        {/* Decorative background gradient */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />
                        
                        <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 relative z-10">
                            <CreditCard className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                            Subscription
                        </h2>

                        <div className="space-y-6 relative z-10">
                            {isPremium ? (
                                <div className="bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-200 dark:border-emerald-800/30 rounded-lg p-5">
                                    <div className="flex items-start gap-3">
                                        <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                                        <div>
                                            <h3 className="font-semibold text-emerald-800 dark:text-emerald-400 mb-1">Premium Plan Active</h3>
                                            <p className="text-sm text-emerald-600 dark:text-emerald-400/80">
                                                You have access to all premium features including Deep Ticker Analysis and priority processing.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
                                        <h3 className="font-semibold mb-2">Upgrade to Premium</h3>
                                        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2 mb-4">
                                            <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-600 dark:text-blue-400" /> Deep Ticker Analysis</li>
                                            <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-600 dark:text-blue-400" /> Higher token limits</li>
                                            <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-600 dark:text-blue-400" /> Priority processing</li>
                                        </ul>
                                    </div>

                                    {isPending ? (
                                        <Button disabled className="w-full">
                                            <Clock className="w-4 h-4 mr-2" />
                                            Upgrade Requested
                                        </Button>
                                    ) : (
                                        <Button 
                                            onClick={() => setShowUpgradeModal(true)}
                                            className="w-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20 transition-all"
                                        >
                                            Request Upgrade to Premium
                                        </Button>
                                    )}
                                </div>
                            )}
                        </div>
                    </Card>
                </div>
            </div>

            {/* Upgrade Request Modal */}
            {showUpgradeModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <Card className="w-full max-w-md p-6 shadow-2xl relative">
                        <div className="flex items-start gap-4 mb-6">
                            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-full">
                                <AlertCircle className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold">Request Premium Plan</h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                    Let us know why you need premium access. An administrator will review your request.
                                </p>
                            </div>
                        </div>

                        <textarea
                            value={upgradeReason}
                            onChange={(e) => setUpgradeReason(e.target.value)}
                            placeholder="I would like to upgrade because..."
                            className="w-full h-32 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 focus:outline-none focus:border-blue-500 dark:focus:border-blue-500 resize-none mb-6"
                        />

                        <div className="flex justify-end gap-3">
                            <Button 
                                variant="outline" 
                                onClick={() => setShowUpgradeModal(false)}
                                disabled={submitting}
                            >
                                Cancel
                            </Button>
                            <Button 
                                onClick={handleUpgradeRequest}
                                disabled={submitting || upgradeReason.length < 10}
                                className="bg-blue-600 hover:bg-blue-700 text-white"
                            >
                                {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                                Submit Request
                            </Button>
                        </div>
                    </Card>
                </div>
            )}
        </div>
    );
}
