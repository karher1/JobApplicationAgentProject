'use client';

import { useState, useEffect } from 'react';
import { analyticsAPI, SearchStatistics, ApplicationStatistics } from '@/lib/api';

export default function AnalyticsPage() {
  const [searchStats, setSearchStats] = useState<SearchStatistics | null>(null);
  const [applicationStats, setApplicationStats] = useState<ApplicationStatistics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [searchData, applicationData] = await Promise.all([
        analyticsAPI.getSearchStatistics(),
        analyticsAPI.getApplicationStatistics(),
      ]);
      setSearchStats(searchData);
      setApplicationStats(applicationData);
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
            Analytics Dashboard
          </h1>
          <p className="text-gray-300 text-lg">
            Track your job search and application performance
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Search Statistics */}
          {searchStats && (
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
              <h2 className="text-2xl font-semibold text-white mb-6">Search Statistics</h2>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-white/10 p-4 rounded-lg">
                  <p className="text-gray-400 text-sm">Total Searches</p>
                  <p className="text-2xl font-bold text-white">{searchStats.total_searches}</p>
                </div>
                <div className="bg-white/10 p-4 rounded-lg">
                  <p className="text-gray-400 text-sm">Jobs Found</p>
                  <p className="text-2xl font-bold text-white">{searchStats.total_jobs_found}</p>
                </div>
                <div className="bg-white/10 p-4 rounded-lg">
                  <p className="text-gray-400 text-sm">Avg Jobs/Search</p>
                  <p className="text-2xl font-bold text-white">{searchStats.average_jobs_per_search.toFixed(1)}</p>
                </div>
              </div>

              {/* Most Searched Titles */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-3">Most Searched Job Titles</h3>
                <div className="space-y-2">
                  {searchStats.most_searched_titles.slice(0, 5).map((item, index) => (
                    <div key={index} className="flex justify-between items-center bg-white/10 p-3 rounded-lg">
                      <span className="text-gray-300">{item.title}</span>
                      <span className="text-white font-semibold">{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Most Searched Locations */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Most Searched Locations</h3>
                <div className="space-y-2">
                  {searchStats.most_searched_locations.slice(0, 5).map((item, index) => (
                    <div key={index} className="flex justify-between items-center bg-white/10 p-3 rounded-lg">
                      <span className="text-gray-300">{item.location}</span>
                      <span className="text-white font-semibold">{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Application Statistics */}
          {applicationStats && (
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
              <h2 className="text-2xl font-semibold text-white mb-6">Application Statistics</h2>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-white/10 p-4 rounded-lg">
                  <p className="text-gray-400 text-sm">Total Applications</p>
                  <p className="text-2xl font-bold text-white">{applicationStats.total_applications}</p>
                </div>
                <div className="bg-white/10 p-4 rounded-lg">
                  <p className="text-gray-400 text-sm">Success Rate</p>
                  <p className="text-2xl font-bold text-white">{(applicationStats.success_rate * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-white/10 p-4 rounded-lg">
                  <p className="text-gray-400 text-sm">Successful</p>
                  <p className="text-2xl font-bold text-green-400">{applicationStats.successful_applications}</p>
                </div>
                <div className="bg-white/10 p-4 rounded-lg">
                  <p className="text-gray-400 text-sm">Failed</p>
                  <p className="text-2xl font-bold text-red-400">{applicationStats.failed_applications}</p>
                </div>
              </div>

              {/* Most Applied Companies */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-3">Most Applied Companies</h3>
                <div className="space-y-2">
                  {applicationStats.most_applied_companies.slice(0, 5).map((item, index) => (
                    <div key={index} className="flex justify-between items-center bg-white/10 p-3 rounded-lg">
                      <span className="text-gray-300">{item.company}</span>
                      <span className="text-white font-semibold">{item.applications}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Average Application Time */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Performance Metrics</h3>
                <div className="bg-white/10 p-4 rounded-lg">
                  <p className="text-gray-400 text-sm">Average Application Time</p>
                  <p className="text-xl font-bold text-white">{applicationStats.average_application_time.toFixed(1)} minutes</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Timeline Charts */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Search Timeline */}
          {searchStats && (
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Search Activity Timeline</h3>
              <div className="space-y-3">
                {searchStats.search_timeline.slice(-7).map((item, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-gray-300 text-sm">{new Date(item.date).toLocaleDateString()}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-blue-400 text-sm">{item.searches} searches</span>
                      <span className="text-green-400 text-sm">{item.jobs_found} jobs</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Application Timeline */}
          {applicationStats && (
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Application Activity Timeline</h3>
              <div className="space-y-3">
                {applicationStats.application_timeline.slice(-7).map((item, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-gray-300 text-sm">{new Date(item.date).toLocaleDateString()}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-blue-400 text-sm">{item.applications} total</span>
                      <span className="text-green-400 text-sm">{item.successful} successful</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Insights */}
        <div className="mt-8 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Key Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {searchStats && (
              <div className="bg-white/10 p-4 rounded-lg">
                <h4 className="text-white font-semibold mb-2">Search Efficiency</h4>
                <p className="text-gray-300 text-sm">
                  You&apos;re finding an average of {searchStats.average_jobs_per_search.toFixed(1)} jobs per search.
                  {searchStats.average_jobs_per_search > 10 ? ' Great job targeting!' : ' Consider broadening your search criteria.'}
                </p>
              </div>
            )}
            
            {applicationStats && (
              <>
                <div className="bg-white/10 p-4 rounded-lg">
                  <h4 className="text-white font-semibold mb-2">Application Success</h4>
                  <p className="text-gray-300 text-sm">
                    Your success rate is {(applicationStats.success_rate * 100).toFixed(1)}%.
                    {applicationStats.success_rate > 0.7 ? ' Excellent performance!' : ' Consider reviewing your application strategy.'}
                  </p>
                </div>
                
                <div className="bg-white/10 p-4 rounded-lg">
                  <h4 className="text-white font-semibold mb-2">Application Speed</h4>
                  <p className="text-gray-300 text-sm">
                    Average application time: {applicationStats.average_application_time.toFixed(1)} minutes.
                    {applicationStats.average_application_time < 5 ? ' Very efficient!' : ' Consider streamlining your process.'}
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 