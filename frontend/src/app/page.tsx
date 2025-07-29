"use client";

import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure } from "@heroui/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { recommendationsAPI, JobPosition, userProfileAPI } from "@/lib/api";
import { tokenUtils } from "@/lib/auth-api";

export default function HomePage() {
  const router = useRouter();
  const [currentJobIndex, setCurrentJobIndex] = useState(0);
  const [jobRecommendations, setJobRecommendations] = useState<JobPosition[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobPosition | null>(null);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState<number | null>(null);
  const [profileCompletion, setProfileCompletion] = useState<{
    isComplete: boolean;
    percentage: number;
    missingFields: string[];
    isAuthenticated: boolean;
  }>({
    isComplete: false,
    percentage: 0,
    missingFields: [],
    isAuthenticated: false
  });
  const { isOpen, onOpen, onClose } = useDisclosure();

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  const calculateProfileCompletion = (profile: Record<string, unknown> | null) => {
    if (!profile) {
      return {
        isComplete: false,
        percentage: 0,
        missingFields: ['Complete profile setup'],
        isAuthenticated: false
      };
    }

    const requiredFields = [
      { field: 'first_name', label: 'First Name' },
      { field: 'last_name', label: 'Last Name' },
      { field: 'email', label: 'Email' },
      { field: 'phone', label: 'Phone Number' },
      { field: 'linkedin_url', label: 'LinkedIn Profile' },
      { field: 'skills', label: 'Skills (at least 3)' },
      { field: 'work_experience', label: 'Work Experience' },
      { field: 'education', label: 'Education' },
      { field: 'resume', label: 'Resume Upload' }
    ];

    const missingFields: string[] = [];
    let completedFields = 0;

    requiredFields.forEach(({ field, label }) => {
      if (field === 'skills') {
        const skills = profile.skills as unknown[] | undefined;
        if (!skills || skills.length < 3) {
          missingFields.push(label);
        } else {
          completedFields++;
        }
      } else if (field === 'work_experience') {
        const workExp = profile.work_experience as unknown[] | undefined;
        if (!workExp || workExp.length === 0) {
          missingFields.push(label);
        } else {
          completedFields++;
        }
      } else if (field === 'education') {
        const education = profile.education as unknown[] | undefined;
        if (!education || education.length === 0) {
          missingFields.push(label);
        } else {
          completedFields++;
        }
      } else if (field === 'resume') {
        const resume = profile.resume as { file_path?: string } | undefined;
        if (!resume || !resume.file_path) {
          missingFields.push(label);
        } else {
          completedFields++;
        }
      } else {
        const fieldValue = profile[field] as string | undefined;
        if (!fieldValue || fieldValue.trim() === '') {
          missingFields.push(label);
        } else {
          completedFields++;
        }
      }
    });

    const percentage = Math.round((completedFields / requiredFields.length) * 100);
    
    return {
      isComplete: percentage >= 80, // Consider 80%+ as complete
      percentage,
      missingFields,
      isAuthenticated: true
    };
  };

  // Load user recommendations and profile completion
  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        const token = tokenUtils.getToken();
        if (token && !tokenUtils.isTokenExpired(token)) {
          setUserId(token.user_id);
          
          // Load profile completion status
          try {
            const profile = await userProfileAPI.getUserProfile(token.user_id);
            const completion = calculateProfileCompletion(profile as unknown as Record<string, unknown>);
            setProfileCompletion(completion);
          } catch (error) {
            console.error('Error loading profile:', error);
            setProfileCompletion({
              isComplete: false,
              percentage: 0,
              missingFields: ['Error loading profile'],
              isAuthenticated: true
            });
          }
          
          const recommendations = await recommendationsAPI.getJobRecommendations(token.user_id, 6);
          setJobRecommendations(recommendations);
        } else {
          // Fallback to sample data for non-authenticated users
          setJobRecommendations([
            {
              id: "sample-1",
              title: "Senior Software Engineer",
              company: "OpenAI",
              location: "Remote",
              salary_min: 180000,
              salary_max: 250000,
              description: "Join our team building the future of AI",
              job_board: "company",
              url: "https://openai.com/careers",
              requirements: ["5+ years experience", "Python", "Machine Learning"],
              benefits: ["Health insurance", "401k", "Remote work"],
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            } as JobPosition,
            {
              id: "sample-2", 
              title: "Frontend Developer",
              company: "Stripe",
              location: "San Francisco",
              salary_min: 150000,
              salary_max: 200000,
              description: "Build beautiful user experiences for financial products",
              job_board: "company",
              url: "https://stripe.com/careers",
              requirements: ["React", "TypeScript", "3+ years experience"],
              benefits: ["Health insurance", "Stock options", "Free lunch"],
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            } as JobPosition
          ]);
        }
      } catch (error) {
        console.error('Error loading recommendations:', error);
        // Fallback to sample data on error
        setJobRecommendations([]);
      } finally {
        setLoading(false);
      }
    };

    loadRecommendations();
  }, []);

  // Auto-rotate job recommendations
  useEffect(() => {
    if (jobRecommendations.length === 0) return;
    const interval = setInterval(() => {
      setCurrentJobIndex((prev) => (prev + 1) % jobRecommendations.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [jobRecommendations.length]);

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return "Salary not specified";
    if (min && max) return `$${(min/1000).toFixed(0)}k - $${(max/1000).toFixed(0)}k`;
    if (min) return `$${(min/1000).toFixed(0)}k+`;
    return "Competitive salary";
  };

  const calculateMatch = () => {
    // Simple match calculation based on requirements overlap
    // In real implementation, this would be calculated by the backend
    return Math.floor(Math.random() * 20) + 80; // 80-99% for demo
  };

  const handleViewDetails = (job: JobPosition) => {
    setSelectedJob(job);
    onOpen();
  };

  return (
    <div className="flex flex-col min-h-[calc(100vh-88px)] items-center justify-center px-4 py-8 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Hero Section */}
      <div className="w-full max-w-3xl text-center mb-12">
        <div className="mb-4">
          <span className="inline-block px-4 py-1 rounded-full bg-white/10 text-xs tracking-widest uppercase text-[#a18fff] mb-4">
            Welcome to Job Application Agent
          </span>
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold mb-6 gradient-text">
          Transform your job search into <span className="gradient-text">beautiful opportunities</span>
        </h1>
        <p className="text-lg text-white/80 mb-8">
          AI-powered job search and application automation. Find your dream job faster with intelligent matching and automated applications.
        </p>
      </div>

      {/* Profile Completion Banner */}
      {profileCompletion.isAuthenticated && !profileCompletion.isComplete && (
        <div className="w-full max-w-3xl mb-8">
          <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-2xl p-6 backdrop-blur-lg">
            <div className="flex items-start gap-4">
              <div className="text-3xl">⚠️</div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-orange-400 mb-2">Complete Your Profile</h3>
                <p className="text-gray-300 mb-4">
                  Your profile is {profileCompletion.percentage}% complete. Complete it to get better job recommendations and enable auto-fill features.
                </p>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-700/50 rounded-full h-2 mb-4">
                  <div 
                    className="bg-gradient-to-r from-orange-500 to-red-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${profileCompletion.percentage}%` }}
                  ></div>
                </div>
                
                {/* Missing Fields */}
                <div className="mb-4">
                  <p className="text-gray-400 text-sm mb-2">Missing information:</p>
                  <div className="flex flex-wrap gap-2">
                    {profileCompletion.missingFields.slice(0, 5).map((field, index) => (
                      <span 
                        key={index}
                        className="px-3 py-1 bg-orange-500/20 text-orange-300 rounded-full text-sm border border-orange-500/30"
                      >
                        {field}
                      </span>
                    ))}
                    {profileCompletion.missingFields.length > 5 && (
                      <span className="px-3 py-1 bg-gray-600/50 text-gray-400 rounded-full text-sm">
                        +{profileCompletion.missingFields.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="flex gap-3">
                  <button
                    onClick={() => handleNavigation('/profile')}
                    className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:scale-105 transition-transform font-medium"
                  >
                    Complete Profile
                  </button>
                  <button
                    onClick={() => setProfileCompletion(prev => ({ ...prev, isComplete: true }))}
                    className="px-4 py-2 bg-gray-600/50 hover:bg-gray-600/70 text-gray-300 rounded-lg transition-colors text-sm"
                  >
                    Remind Later
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Job Recommendation Carousel */}
      {!loading && jobRecommendations.length > 0 && (
        <div className="w-full max-w-3xl mb-12">
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 relative overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">🎯 Recommended for You</h3>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 text-sm rounded-full border border-green-500/30">
                {calculateMatch()}% Match
              </span>
            </div>
            
            <div className="transition-all duration-500 ease-in-out">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h4 className="text-xl font-semibold text-white mb-2">
                    {jobRecommendations[currentJobIndex].title}
                  </h4>
                  <p className="text-blue-400 font-medium mb-1">
                    {jobRecommendations[currentJobIndex].company}
                  </p>
                  <div className="flex items-center gap-4 text-gray-300 text-sm">
                    <span>📍 {jobRecommendations[currentJobIndex].location}</span>
                    <span>💰 {formatSalary(jobRecommendations[currentJobIndex].salary_min, jobRecommendations[currentJobIndex].salary_max)}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 ml-6">
                  <button
                    onClick={() => handleViewDetails(jobRecommendations[currentJobIndex])}
                    className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:scale-105 transition-transform font-medium"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => handleNavigation('/chat')}
                    className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors border border-white/20"
                  >
                    Apply Now
                  </button>
                </div>
              </div>
            </div>
            
            {/* Carousel indicators */}
            <div className="flex justify-center gap-2 mt-4">
              {jobRecommendations.map((_, index) => (
                <button
                  key={index}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index === currentJobIndex ? 'bg-blue-500' : 'bg-white/30'
                  }`}
                  onClick={() => setCurrentJobIndex(index)}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div 
          onClick={() => handleNavigation('/job-search')}
          className="group cursor-pointer"
        >
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/20 active:scale-95">
            <div className="text-4xl mb-4 group-hover:scale-110 group-hover:animate-pulse transition-transform duration-300">🔍</div>
            <h3 className="text-xl font-semibold text-white mb-2">Browse Jobs</h3>
            <p className="text-gray-400 text-sm">Discover thousands of job opportunities</p>
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/0 via-blue-500/5 to-purple-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>
        </div>

        <div 
          onClick={() => handleNavigation('/chat')}
          className="group cursor-pointer relative"
        >
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/20 active:scale-95">
            <div className="text-4xl mb-4 group-hover:scale-110 group-hover:animate-pulse transition-transform duration-300">🤖</div>
            <h3 className="text-xl font-semibold text-white mb-2">AI Assistant</h3>
            <p className="text-gray-400 text-sm">Get personalized career guidance</p>
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-purple-500/0 via-purple-500/5 to-pink-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>
        </div>

        <div 
          onClick={() => handleNavigation('/applications')}
          className="group cursor-pointer relative"
        >
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-green-500/20 active:scale-95">
            <div className="text-4xl mb-4 group-hover:scale-110 group-hover:animate-pulse transition-transform duration-300">📋</div>
            <h3 className="text-xl font-semibold text-white mb-2">Applications</h3>
            <p className="text-gray-400 text-sm">Track your application progress</p>
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-green-500/0 via-green-500/5 to-emerald-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>
        </div>

        <div 
          onClick={() => handleNavigation('/analytics')}
          className="group cursor-pointer relative"
        >
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-orange-500/20 active:scale-95">
            <div className="text-4xl mb-4 group-hover:scale-110 group-hover:animate-pulse transition-transform duration-300">📊</div>
            <h3 className="text-xl font-semibold text-white mb-2">Analytics</h3>
            <p className="text-gray-400 text-sm">View your job search insights</p>
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-orange-500/0 via-orange-500/5 to-yellow-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>
        </div>
      </div>

      {/* Features Preview */}
      <div className="w-full max-w-4xl mt-16">
        <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-8">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">Why Choose Our Platform?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">AI</span>
              </div>
              <h3 className="text-white font-semibold mb-2">AI-Powered</h3>
              <p className="text-gray-400 text-sm">Smart job matching and resume optimization</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-4 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">⚡</span>
              </div>
              <h3 className="text-white font-semibold mb-2">Lightning Fast</h3>
              <p className="text-gray-400 text-sm">Apply to multiple jobs in seconds</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">🎯</span>
              </div>
              <h3 className="text-white font-semibold mb-2">Smart Targeting</h3>
              <p className="text-gray-400 text-sm">Find jobs that match your skills perfectly</p>
            </div>
          </div>
        </div>
      </div>

      {/* Job Details Modal */}
      <Modal 
        isOpen={isOpen} 
        onClose={onClose}
        size="3xl"
        scrollBehavior="inside"
        className="bg-slate-800 text-white"
        classNames={{
          base: "bg-slate-800 border border-white/10",
          header: "border-b border-white/10",
          body: "text-white",
          footer: "border-t border-white/10",
        }}
      >
        <ModalContent>
          <ModalHeader>
            <h3 className="text-xl font-semibold">Job Details</h3>
          </ModalHeader>
          <ModalBody>
            {selectedJob && (
              <div className="space-y-6">
                {/* Job Header */}
                <div className="text-center pb-4 border-b border-white/10">
                  <h2 className="text-2xl font-bold text-white mb-2">{selectedJob.title}</h2>
                  <p className="text-blue-400 text-lg font-medium">{selectedJob.company}</p>
                  <div className="flex items-center justify-center gap-6 mt-4 text-gray-300">
                    <span className="flex items-center gap-1">
                      📍 {selectedJob.location}
                    </span>
                    <span className="flex items-center gap-1">
                      💰 {formatSalary(selectedJob.salary_min, selectedJob.salary_max)}
                    </span>
                    <span className="flex items-center gap-1 px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
                      {calculateMatch()}% Match
                    </span>
                  </div>
                </div>

                {/* Job Description */}
                {selectedJob.description && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">About the Role</h4>
                    <p className="text-gray-300 leading-relaxed">{selectedJob.description}</p>
                  </div>
                )}

                {/* Requirements */}
                {selectedJob.requirements && selectedJob.requirements.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Requirements</h4>
                    <ul className="space-y-2">
                      {selectedJob.requirements.map((req, index) => (
                        <li key={index} className="flex items-start gap-2 text-gray-300">
                          <span className="text-blue-400 mt-1">•</span>
                          <span>{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Benefits */}
                {selectedJob.benefits && selectedJob.benefits.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Benefits</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedJob.benefits.map((benefit, index) => (
                        <span key={index} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm border border-purple-500/30">
                          {benefit}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Job Board Info */}
                <div className="bg-white/5 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Posted on: <span className="text-white">{selectedJob.job_board}</span></span>
                    <span className="text-gray-400">
                      {new Date(selectedJob.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </ModalBody>
          <ModalFooter>
            <Button
              color="default"
              variant="light"
              onPress={onClose}
            >
              Close
            </Button>
            <Button
              color="primary"
              onPress={() => {
                if (selectedJob?.url) {
                  window.open(selectedJob.url, '_blank');
                }
              }}
              className="bg-gradient-to-r from-blue-500 to-purple-500"
            >
              Apply on {selectedJob?.job_board}
            </Button>
            <Button
              color="secondary"
              onPress={() => {
                onClose();
                handleNavigation('/chat');
              }}
              className="bg-gradient-to-r from-purple-500 to-pink-500"
            >
              Apply with AI Assistant
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
