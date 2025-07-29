'use client';

import { useState, useEffect } from 'react';
import { Card } from "@heroui/react";
import { jobSearchAPI, JobPosition, JobSearchRequest } from '@/lib/api';
import CompanySelector from '@/components/company-selector';
import CacheManager from '@/components/cache-manager';

interface SearchFilters {
  job_titles: string[];
  locations: string[];
  companies: string[];
  max_results: number;
  job_boards: string[];
  remote_only: boolean;
}

// Loading messages that change over time
const loadingMessages = [
  {
    message: "🔍 Scanning job boards...",
    description: "We're searching across multiple platforms to find the best opportunities for you."
  },
  {
    message: "🏢 Checking company career pages...",
    description: "Looking through direct company listings for fresh opportunities."
  },
  {
    message: "📊 Filtering and analyzing jobs...",
    description: "Matching your criteria and analyzing job descriptions."
  },
  {
    message: "✨ Almost there! Finalizing results...",
    description: "Preparing your personalized job recommendations."
  }
];

// Predefined job title suggestions
const jobTitleSuggestions = [
  'Software Engineer',
  'Frontend Developer',
  'Backend Developer',
  'Full Stack Developer',
  'Data Scientist',
  'Machine Learning Engineer',
  'Product Manager',
  'DevOps Engineer',
  'UI/UX Designer',
  'Data Engineer',
  'Software Architect',
  'Technical Lead',
  'Site Reliability Engineer',
  'Mobile Developer',
  'Cloud Engineer'
];

// Predefined location suggestions
const locationSuggestions = [
  'Remote',
  'San Francisco, CA',
  'New York, NY',
  'Seattle, WA',
  'Austin, TX',
  'Boston, MA',
  'Los Angeles, CA',
  'Chicago, IL',
  'Denver, CO',
  'Portland, OR',
  'Remote US',
  'Remote Europe',
  'Remote Global'
];

export default function JobSearchPage() {
  const [jobs, setJobs] = useState<JobPosition[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState<number | null>(null);
  const [currentLoadingMessage, setCurrentLoadingMessage] = useState(0);
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    job_titles: ['Software Engineer'],
    locations: [],
    companies: [],
    max_results: 20,
    job_boards: [],
    remote_only: false,
  });
  const [totalJobs, setTotalJobs] = useState(0);
  const [showCacheManager, setShowCacheManager] = useState(false);
  
  // Input states for better UX
  const [jobTitleInput, setJobTitleInput] = useState('Software Engineer');
  const [locationInput, setLocationInput] = useState('');
  const [showJobTitleSuggestions, setShowJobTitleSuggestions] = useState(false);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);

  // Update loading message every 15 seconds
  useEffect(() => {
    if (loading && loadingStartTime) {
      const interval = setInterval(() => {
        setCurrentLoadingMessage(prev => (prev + 1) % loadingMessages.length);
      }, 15000);

      return () => clearInterval(interval);
    }
  }, [loading, loadingStartTime]);

  const handleSearch = async () => {
    setLoading(true);
    setLoadingStartTime(Date.now());
    setCurrentLoadingMessage(0);
    try {
      let response;
      
      // If companies are selected, use the company-specific search endpoint
      if (searchFilters.companies.length > 0) {
        const companyRequest = {
          job_titles: searchFilters.job_titles,
          companies: searchFilters.companies,
          locations: searchFilters.locations.filter(loc => loc.trim() !== ''),
          max_results: searchFilters.max_results,
          remote_only: searchFilters.remote_only,
        };
        response = await jobSearchAPI.searchJobsByCompanies(companyRequest);
      } else {
        // Use the general search endpoint
        const request: JobSearchRequest = {
          job_titles: searchFilters.job_titles,
          locations: searchFilters.locations.filter(loc => loc.trim() !== ''),
          companies: searchFilters.companies,
          max_results: searchFilters.max_results,
          job_boards: searchFilters.job_boards,
          remote_only: searchFilters.remote_only,
        };
        response = await jobSearchAPI.searchJobs(request);
      }
      
      setJobs(Array.isArray(response) ? response : (response.jobs || []));
      setTotalJobs(Array.isArray(response) ? response.length : (response.total_jobs_found || 0));
    } catch (error) {
      console.error('Error searching jobs:', error);
    } finally {
      setLoading(false);
      setLoadingStartTime(null);
    }
  };

  const handleJobTitleInputChange = (value: string) => {
    setJobTitleInput(value);
    const titles = value.split(',').map(t => t.trim()).filter(t => t);
    setSearchFilters(prev => ({ ...prev, job_titles: titles }));
  };

  const handleLocationInputChange = (value: string) => {
    setLocationInput(value);
    const locations = value.split(',').map(l => l.trim()).filter(l => l);
    setSearchFilters(prev => ({ ...prev, locations }));
  };

  const addJobTitleSuggestion = (title: string) => {
    const currentTitles = jobTitleInput.split(',').map(t => t.trim()).filter(t => t);
    if (!currentTitles.includes(title)) {
      const newInput = currentTitles.length > 0 ? `${jobTitleInput}, ${title}` : title;
      handleJobTitleInputChange(newInput);
    }
    setShowJobTitleSuggestions(false);
  };

  const addLocationSuggestion = (location: string) => {
    const currentLocations = locationInput.split(',').map(l => l.trim()).filter(l => l);
    if (!currentLocations.includes(location)) {
      const newInput = currentLocations.length > 0 ? `${locationInput}, ${location}` : location;
      handleLocationInputChange(newInput);
    }
    setShowLocationSuggestions(false);
  };

  const handleCompanyChange = (companies: string[]) => {
    setSearchFilters(prev => ({ ...prev, companies }));
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getElapsedTime = () => {
    if (!loadingStartTime) return 0;
    return Math.floor((Date.now() - loadingStartTime) / 1000);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatSalary = (salary?: string) => {
    if (!salary || salary === '$0-$0') return 'Not specified';
    return salary;
  };

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-4">
              Find Your Next <span className="gradient-text">Dream Job</span>
            </h1>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              Search across top tech companies and job boards. Get real-time results with intelligent caching.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Search Filters - Modern Card Design */}
            <div className="lg:col-span-1">
              <Card className="sticky top-4 shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Search Filters</h2>
                    <button
                      onClick={() => setShowCacheManager(!showCacheManager)}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Cache Manager
                    </button>
                  </div>
                  
                  <div className="space-y-6">
                    {/* Job Titles with Suggestions */}
                    <div className="relative">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Job Titles
                      </label>
                      <div className="relative">
                        <input
                          type="text"
                          value={jobTitleInput}
                          onChange={(e) => handleJobTitleInputChange(e.target.value)}
                          onFocus={() => setShowJobTitleSuggestions(true)}
                          onBlur={() => setTimeout(() => setShowJobTitleSuggestions(false), 200)}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                          placeholder="e.g., Software Engineer, Data Scientist"
                        />
                        <div className="absolute right-3 top-3 text-gray-400">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                        </div>
                      </div>
                      {showJobTitleSuggestions && (
                        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg max-h-60 overflow-y-auto">
                          {jobTitleSuggestions.map((title) => (
                            <button
                              key={title}
                              onClick={() => addJobTitleSuggestion(title)}
                              className="w-full px-4 py-2 text-left hover:bg-blue-50 hover:text-blue-700 transition-colors duration-150 first:rounded-t-xl last:rounded-b-xl"
                            >
                              {title}
                            </button>
                          ))}
                        </div>
                      )}
                      <p className="text-xs text-gray-500 mt-1">Separate multiple titles with commas</p>
                    </div>

                    {/* Locations with Suggestions */}
                    <div className="relative">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Locations (Optional)
                      </label>
                      <div className="relative">
                        <input
                          type="text"
                          value={locationInput}
                          onChange={(e) => handleLocationInputChange(e.target.value)}
                          onFocus={() => setShowLocationSuggestions(true)}
                          onBlur={() => setTimeout(() => setShowLocationSuggestions(false), 200)}
                          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                          placeholder="e.g., Remote, San Francisco, New York"
                        />
                        <div className="absolute right-3 top-3 text-gray-400">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        </div>
                      </div>
                      {showLocationSuggestions && (
                        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg max-h-60 overflow-y-auto">
                          {locationSuggestions.map((location) => (
                            <button
                              key={location}
                              onClick={() => addLocationSuggestion(location)}
                              className="w-full px-4 py-2 text-left hover:bg-blue-50 hover:text-blue-700 transition-colors duration-150 first:rounded-t-xl last:rounded-b-xl"
                            >
                              {location}
                            </button>
                          ))}
                        </div>
                      )}
                      <p className="text-xs text-gray-500 mt-1">Leave empty to search all locations</p>
                    </div>

                    {/* Companies */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Companies (Max 5)
                      </label>
                      <CompanySelector
                        selectedCompanies={searchFilters.companies}
                        onCompaniesChange={handleCompanyChange}
                      />
                    </div>

                    {/* Remote Only Toggle */}
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        id="remote-only"
                        checked={searchFilters.remote_only}
                        onChange={(e) => setSearchFilters(prev => ({ ...prev, remote_only: e.target.checked }))}
                        className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                      />
                      <label htmlFor="remote-only" className="text-sm font-medium text-gray-700">
                        Remote positions only
                      </label>
                    </div>

                    {/* Max Results */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Max Results: {searchFilters.max_results}
                      </label>
                      <input
                        type="range"
                        min="5"
                        max="50"
                        value={searchFilters.max_results}
                        onChange={(e) => setSearchFilters(prev => ({ ...prev, max_results: parseInt(e.target.value) }))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>5</span>
                        <span>50</span>
                      </div>
                    </div>

                    {/* Search Button */}
                    <button
                      onClick={handleSearch}
                      disabled={loading}
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                    >
                      {loading ? (
                        <div className="flex items-center justify-center space-x-2">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                          <span>Searching...</span>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center space-x-2">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                          <span>Search Jobs</span>
                        </div>
                      )}
                    </button>
                  </div>
                </div>
              </Card>

              {/* Cache Manager */}
              {showCacheManager && (
                <div className="mt-4">
                  <CacheManager />
                </div>
              )}
            </div>

            {/* Results Section */}
            <div className="lg:col-span-2">
              {/* Loading State */}
              {loading && (
                <Card className="mb-6 shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                  <div className="p-8 text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {loadingMessages[currentLoadingMessage].message}
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {loadingMessages[currentLoadingMessage].description}
                    </p>
                    <div className="text-sm text-gray-500">
                      Elapsed time: {formatTime(getElapsedTime())}
                    </div>
                  </div>
                </Card>
              )}

              {/* Results Header */}
              {!loading && jobs.length > 0 && (
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Found {totalJobs} Jobs
                  </h2>
                  <p className="text-gray-600">
                    Showing results for: {searchFilters.job_titles.join(', ')}
                    {searchFilters.companies.length > 0 && ` at ${searchFilters.companies.join(', ')}`}
                  </p>
                </div>
              )}

              {/* Job Results */}
              <div className="space-y-4">
                {jobs.map((job, index) => (
                  <Card key={index} className="shadow-lg border-0 bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-200 transform hover:scale-[1.02]">
                    <div className="p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-900 mb-2">
                            {job.title}
                          </h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                            <div className="flex items-center space-x-1">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                              </svg>
                              <span className="font-medium">{job.company}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                              <span>{job.location || 'Location not specified'}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex flex-col items-end space-y-2">
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {job.job_board}
                          </span>
                          {job.remote_option === 'Remote' && (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              🌍 Remote
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <div className="flex items-center space-x-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                            <span>{formatSalary(job.salary_range)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <span>Posted {formatDate(job.posted_date)}</span>
                          </div>
                        </div>
                      </div>

                      {job.description_snippet && (
                        <div className="mb-4">
                          <p className="text-gray-700 text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: job.description_snippet.substring(0, 200) + '...' }} />
                        </div>
                      )}

                      <div className="flex justify-between items-center">
                        <div className="flex items-center space-x-2">
                          {job.job_type && (
                            <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800">
                              {job.job_type}
                            </span>
                          )}
                        </div>
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200"
                        >
                          Apply Now
                          <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              {/* No Results */}
              {!loading && jobs.length === 0 && (
                <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                  <div className="p-8 text-center">
                    <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No jobs found</h3>
                    <p className="text-gray-600 mb-4">
                      Try adjusting your search criteria or check back later for new opportunities.
                    </p>
                    <button
                      onClick={handleSearch}
                      className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200"
                    >
                      Search Again
                    </button>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 