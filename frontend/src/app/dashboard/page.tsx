'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { analyticsAPI, SearchStatistics, ApplicationStatistics } from '@/lib/api';

export default function DashboardPage() {
  const [searchStats, setSearchStats] = useState<SearchStatistics | null>(null);
  const [applicationStats, setApplicationStats] = useState<ApplicationStatistics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [searchData, applicationData] = await Promise.all([
        analyticsAPI.getSearchStatistics(),
        analyticsAPI.getApplicationStatistics(),
      ]);
      setSearchStats(searchData);
      setApplicationStats(applicationData);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      title: 'Job Search',
      description: 'Search for jobs across multiple platforms with AI-powered filtering',
      href: '/job-search',
      icon: '🔍',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      title: 'Profile Management',
      description: 'Manage your professional profile, skills, and preferences',
      href: '/profile',
      icon: '👤',
      color: 'from-purple-500 to-pink-500'
    },
    {
      title: 'Applications',
      description: 'Track and manage your job applications with review system',
      href: '/applications',
      icon: '📝',
      color: 'from-green-500 to-emerald-500'
    },
    {
      title: 'Analytics',
      description: 'View detailed analytics and insights about your job search',
      href: '/analytics',
      icon: '📊',
      color: 'from-orange-500 to-red-500'
    },
    {
      title: 'Recommendations',
      description: 'Get AI-powered job recommendations based on your profile',
      href: '/recommendations',
      icon: '🎯',
      color: 'from-indigo-500 to-purple-500'
    },
    {
      title: 'AI Assistant',
      description: 'Chat with AI for career guidance, job search help, and resume advice',
      href: '/chat',
      icon: '🤖',
      color: 'from-pink-500 to-rose-500'
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-6">
            Dashboard
          </h1>
          <p className="text-gray-300 text-xl">
            Welcome to your AI-powered job search dashboard
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
            <div className="text-3xl mb-2">🔍</div>
            <h3 className="text-white font-semibold mb-1">Total Searches</h3>
            <p className="text-2xl font-bold text-blue-400">
              {searchStats?.total_searches || 0}
            </p>
          </div>
          
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
            <div className="text-3xl mb-2">💼</div>
            <h3 className="text-white font-semibold mb-1">Jobs Found</h3>
            <p className="text-2xl font-bold text-green-400">
              {searchStats?.total_jobs_found || 0}
            </p>
          </div>
          
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
            <div className="text-3xl mb-2">📝</div>
            <h3 className="text-white font-semibold mb-1">Applications</h3>
            <p className="text-2xl font-bold text-purple-400">
              {applicationStats?.total_applications || 0}
            </p>
          </div>
          
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
            <div className="text-3xl mb-2">📈</div>
            <h3 className="text-white font-semibold mb-1">Success Rate</h3>
            <p className="text-2xl font-bold text-orange-400">
              {applicationStats ? `${(applicationStats.success_rate * 100).toFixed(1)}%` : '0%'}
            </p>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Link key={index} href={feature.href}>
                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-all cursor-pointer group">
                  <div className="text-4xl mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
                  <p className="text-gray-300 text-sm leading-relaxed">{feature.description}</p>
                  <div className={`mt-4 w-0 group-hover:w-full h-1 bg-gradient-to-r ${feature.color} transition-all duration-300 rounded-full`}></div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Searches */}
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Recent Search Activity</h3>
            {searchStats?.search_timeline.slice(-5).map((item, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b border-white/10 last:border-b-0">
                <span className="text-gray-300 text-sm">
                  {new Date(item.date).toLocaleDateString()}
                </span>
                <div className="flex gap-4 text-sm">
                  <span className="text-blue-400">{item.searches} searches</span>
                  <span className="text-green-400">{item.jobs_found} jobs</span>
                </div>
              </div>
            ))}
          </div>

          {/* Recent Applications */}
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Recent Application Activity</h3>
            {applicationStats?.application_timeline.slice(-5).map((item, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b border-white/10 last:border-b-0">
                <span className="text-gray-300 text-sm">
                  {new Date(item.date).toLocaleDateString()}
                </span>
                <div className="flex gap-4 text-sm">
                  <span className="text-purple-400">{item.applications} total</span>
                  <span className="text-green-400">{item.successful} successful</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-12 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-8">
          <h3 className="text-2xl font-semibold text-white mb-6 text-center">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Link href="/job-search">
              <button className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-4 px-6 rounded-lg font-semibold hover:from-blue-600 hover:to-cyan-600 transition-all">
                🔍 Start Job Search
              </button>
            </Link>
            
            <Link href="/chat">
              <button className="w-full bg-gradient-to-r from-pink-500 to-rose-500 text-white py-4 px-6 rounded-lg font-semibold hover:from-pink-600 hover:to-rose-600 transition-all">
                🤖 AI Assistant
              </button>
            </Link>
            
            <Link href="/profile">
              <button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-4 px-6 rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition-all">
                👤 Update Profile
              </button>
            </Link>
            
            <Link href="/recommendations">
              <button className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white py-4 px-6 rounded-lg font-semibold hover:from-green-600 hover:to-emerald-600 transition-all">
                🎯 Get Recommendations
              </button>
            </Link>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-8 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">💡 Pro Tips</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-300">
            <div>
              <strong className="text-white">Complete Your Profile:</strong> Add your skills, experience, and preferences to get better job recommendations.
            </div>
            <div>
              <strong className="text-white">Upload Your Resume:</strong> Having a primary resume uploaded enables automatic job applications.
            </div>
            <div>
              <strong className="text-white">Use Analytics:</strong> Track your search patterns and application success rates to optimize your strategy.
            </div>
            <div>
              <strong className="text-white">Review Applications:</strong> Check your pending applications and approve or reject them as needed.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 