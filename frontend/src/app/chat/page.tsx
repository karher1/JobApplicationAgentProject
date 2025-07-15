'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { tokenUtils } from '@/lib/auth-api';
import ChatInterface from '@/components/chat-interface';

export default function ChatPage() {
  const [userId, setUserId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Skip authentication for now - TODO: Implement proper auth
    // const token = tokenUtils.getToken();
    // if (!token || tokenUtils.isTokenExpired(token)) {
    //   router.push('/login');
    //   return;
    // }
    
    // For now, use a default user ID. In a real app, get from token
    setUserId(1);
    setIsLoading(false);
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!userId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white">Please log in to access the chat.</div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-88px)] bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col">
      <div className="flex-shrink-0 p-4 pb-2">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white mb-1">AI Career Assistant</h1>
            <p className="text-gray-300 text-xs">Get personalized career guidance and job search assistance</p>
          </div>
          <button
            onClick={() => router.push('/')}
            className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-sm rounded-lg border border-white/20 transition-colors"
          >
            ← Back to Home
          </button>
        </div>
      </div>
      <div className="flex-1 px-4 pb-4 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full">
          <ChatInterface userId={userId} />
        </div>
      </div>
    </div>
  );
} 