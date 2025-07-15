'use client';

import { useState, useEffect } from 'react';
import { recommendationsAPI, JobPosition, JobMatchResponse } from '@/lib/api';

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<JobPosition[]>([]);
  const [matches, setMatches] = useState<JobMatchResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [jobDescription, setJobDescription] = useState('');
  const [matchingLoading, setMatchingLoading] = useState(false);

  // Mock user ID - in real app, get from auth context
  const userId = 1;

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      const jobs = await recommendationsAPI.getJobRecommendations(userId, 20);
      setRecommendations(jobs);
    } catch (error) {
      console.error('Error loading recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMatchJobs = async () => {
    if (!jobDescription.trim()) return;

    setMatchingLoading(true);
    try {
      const jobMatches = await recommendationsAPI.matchJobsForUser(userId, jobDescription, 10);
      setMatches(jobMatches);
    } catch (error) {
      console.error('Error matching jobs:', error);
    } finally {
      setMatchingLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400';
    if (score >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white">Loading recommendations...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
            Job Recommendations
          </h1>
          <p className="text-gray-300 text-lg">
            AI-powered job recommendations based on your profile
          </p>
        </div>

        {/* Job Matching Section */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold text-white mb-4">Match Jobs to Your Profile</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-gray-300 mb-2">Job Description</label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste a job description to find similar jobs and get match scores..."
                className="w-full h-32 bg-white/10 border border-white/20 rounded-lg p-3 text-white placeholder-gray-400 resize-none"
              />
            </div>
            <button
              onClick={handleMatchJobs}
              disabled={matchingLoading || !jobDescription.trim()}
              className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-2 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {matchingLoading ? 'Matching...' : 'Find Similar Jobs'}
            </button>
          </div>
        </div>

        {/* Job Matches */}
        {matches.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">Job Matches</h2>
            <div className="grid gap-4">
              {matches.map((match, index) => (
                <div key={index} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-white mb-2">
                        {match.title}
                      </h3>
                      <p className="text-gray-300 mb-2">{match.company}</p>
                      <div className="flex items-center gap-4 text-gray-400 text-sm">
                        <span>Match Score: <span className={getMatchScoreColor(match.match_score)}>{(match.match_score * 100).toFixed(1)}%</span></span>
                        <span>Experience Match: {match.experience_match ? '✓' : '✗'}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${getMatchScoreColor(match.match_score)}`}>
                        {(match.match_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  {/* Match Reasons */}
                  <div className="mb-4">
                    <h4 className="text-white font-semibold mb-2">Why this matches:</h4>
                    <div className="flex flex-wrap gap-2">
                      {match.match_reasons.map((reason, idx) => (
                        <span key={idx} className="bg-blue-500/20 text-blue-300 px-2 py-1 rounded text-sm">
                          {reason}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Skills Match */}
                  {match.skills_match.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-white font-semibold mb-2">Matching Skills:</h4>
                      <div className="flex flex-wrap gap-2">
                        {match.skills_match.map((skill, idx) => (
                          <span key={idx} className="bg-green-500/20 text-green-300 px-2 py-1 rounded text-sm">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-between items-center">
                    <button className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-lg font-semibold">
                      View Job
                    </button>
                    <button className="bg-white/10 text-white px-4 py-2 rounded-lg font-semibold border border-white/20">
                      Apply Now
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Recommendations */}
        <div>
          <h2 className="text-2xl font-semibold text-white mb-4">AI Recommendations</h2>
          <div className="grid gap-4">
            {recommendations.map((job, index) => (
              <div key={job.id || index} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-all">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-white mb-2">
                      {job.title}
                    </h3>
                    <p className="text-gray-300 mb-2">{job.company}</p>
                    <div className="flex items-center gap-4 text-gray-400 text-sm">
                      <span>{job.location}</span>
                      {job.posted_date && (
                        <span>Posted: {formatDate(job.posted_date)}</span>
                      )}
                      <span>Source: {job.job_board}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    {job.job_type && (
                      <span className="bg-blue-500/20 text-blue-300 px-2 py-1 rounded text-sm">
                        {job.job_type}
                      </span>
                    )}
                    {job.remote_option && (
                      <span className="bg-green-500/20 text-green-300 px-2 py-1 rounded text-sm">
                        {job.remote_option}
                      </span>
                    )}
                  </div>
                </div>

                {job.salary_range && (
                  <div className="mb-4">
                    <span className="text-gray-300 font-semibold">Salary: {job.salary_range}</span>
                  </div>
                )}

                {job.description_snippet && (
                  <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                    {job.description_snippet}
                  </p>
                )}

                <div className="flex justify-between items-center">
                  <button className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-lg font-semibold">
                    View Job
                  </button>
                  <button className="bg-white/10 text-white px-4 py-2 rounded-lg font-semibold border border-white/20">
                    Apply Now
                  </button>
                </div>
              </div>
            ))}
          </div>

          {recommendations.length === 0 && (
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-12 text-center">
              <p className="text-gray-400 text-lg">
                No recommendations available. Update your profile preferences to get personalized recommendations.
              </p>
            </div>
          )}
        </div>

        {/* Insights */}
        <div className="mt-8 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Recommendation Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-white/10 p-4 rounded-lg">
              <h4 className="text-white font-semibold mb-2">Based on Your Skills</h4>
              <p className="text-gray-300 text-sm">
                Recommendations are tailored to your listed skills and experience level.
              </p>
            </div>
            
            <div className="bg-white/10 p-4 rounded-lg">
              <h4 className="text-white font-semibold mb-2">Location Preferences</h4>
              <p className="text-gray-300 text-sm">
                Jobs are filtered based on your preferred locations and remote preferences.
              </p>
            </div>
            
            <div className="bg-white/10 p-4 rounded-lg">
              <h4 className="text-white font-semibold mb-2">Salary Range</h4>
              <p className="text-gray-300 text-sm">
                Recommendations consider your salary expectations and experience level.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 