'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardBody, Button, Progress, Chip, Textarea } from '@heroui/react';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  ChartBarIcon,
  LightBulbIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

interface ResumeAnalysisResults {
  overall_score: number;
  ats_compatibility: {
    score: number;
    issues: string[];
    recommendations: string[];
  };
  content_strength: {
    score: number;
    strengths: string[];
    weaknesses: string[];
    feedback: string[];
  };
  keyword_optimization: {
    keyword_match_score: number;
    missing_keywords: string[];
    present_keywords: string[];
    recommendations: string[];
  };
  improvement_suggestions: Array<{
    category: string;
    priority: string;
    suggestion: string;
    example: string;
  }>;
}

interface OptimizationResult {
  original_score: number;
  optimized_score: number;
  original_content: string;
  optimized_content: string;
  improvements: string[];
  changes: string[];
  score_improvement: number;
  improvements_made: string[];
  keyword_additions: string[];
  optimized_resume: string;
}


export default function ResumeAnalysisPage() {
  const [resumeText, setResumeText] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResults, setAnalysisResults] = useState<ResumeAnalysisResults | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState<'analyze' | 'optimize'>('analyze');
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Check if it's a text file or PDF/DOC
      if (file.type === 'text/plain') {
        // Read text files directly
        const reader = new FileReader();
        reader.onload = (e) => {
          const text = e.target?.result as string;
          setResumeText(text);
        };
        reader.readAsText(file);
      } else {
        // For PDF/DOC files, clear the text field and use file upload endpoint
        setResumeText('');
        alert('PDF/DOC file selected. Click "Analyze Resume" to process the file.');
      }
    }
  };

  const analyzeResume = async () => {
    // Check if we have either text content or a selected file
    if (!resumeText.trim() && !selectedFile) {
      alert('Please provide resume text or upload a file');
      return;
    }

    setIsAnalyzing(true);
    try {
      let response;
      
      // If we have a selected file (PDF/DOC), use the file upload endpoint
      if (selectedFile && selectedFile.type !== 'text/plain') {
        const formData = new FormData();
        formData.append('file', selectedFile);
        if (jobDescription.trim()) {
          formData.append('job_description', jobDescription);
        }
        
        response = await fetch('http://localhost:8000/api/resume-analysis/analyze-file', {
          method: 'POST',
          body: formData,
        });
      } else {
        // Use text analysis endpoint for plain text
        response = await fetch('http://localhost:8000/api/resume-analysis/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            resume_text: resumeText,
            job_description: jobDescription || null,
          }),
        });
      }

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setAnalysisResults(data.analysis);
    } catch (error) {
      console.error('Error analyzing resume:', error);
      alert('Failed to analyze resume. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const optimizeResume = async () => {
    if (!resumeText.trim() || !jobDescription.trim()) {
      alert('Please provide both resume text and job description for optimization');
      return;
    }

    setIsOptimizing(true);
    try {
      const formData = new FormData();
      formData.append('resume_text', resumeText);
      formData.append('job_description', jobDescription);
      
      const response = await fetch('http://localhost:8000/api/resume-analysis/optimize', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Optimization failed');
      }

      const data = await response.json();
      setOptimizationResult(data.optimization);
    } catch (error) {
      console.error('Error optimizing resume:', error);
      alert('Failed to optimize resume. Please try again.');
    } finally {
      setIsOptimizing(false);
    }
  };


  const getScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'danger';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return 'danger';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          🔍 AI Resume Analysis & Optimization
        </h1>
        <p className="text-lg text-gray-600">
          Get comprehensive insights and ATS optimization for your resume
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-4 mb-6">
        {[
          { id: 'analyze', label: 'Analyze Resume', icon: ChartBarIcon },
          { id: 'optimize', label: 'Optimize Resume', icon: SparklesIcon },
        ].map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? 'solid' : 'bordered'}
            color={activeTab === tab.id ? 'primary' : 'default'}
            onClick={() => setActiveTab(tab.id as any)}
            startContent={<tab.icon className="w-4 h-4" />}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Resume & Job Details</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Upload Resume File (Optional)
              </label>
              <input
                type="file"
                accept=".txt,.pdf,.doc,.docx"
                onChange={handleFileUpload}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100"
              />
              {selectedFile && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {selectedFile.name}
                </p>
              )}
            </div>

            {/* Resume Text Input */}
            <Textarea
              label="Resume Text"
              placeholder="Paste your resume text here or upload a file above..."
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              minRows={8}
              maxRows={12}
              variant="bordered"
            />

            {/* Job Description Input */}
            <Textarea
              label="Job Description (Optional - for targeted analysis)"
              placeholder="Paste the job description to get recommendations specific to this role..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              minRows={4}
              maxRows={8}
              variant="bordered"
            />

            {/* Action Buttons */}
            <div className="flex space-x-3">
              {activeTab === 'analyze' ? (
                <Button
                  color="primary"
                  onClick={analyzeResume}
                  isLoading={isAnalyzing}
                  isDisabled={!resumeText.trim() && !selectedFile}
                  startContent={<ChartBarIcon className="w-4 h-4" />}
                  className="w-full"
                  size="lg"
                >
                  {isAnalyzing ? 'Analyzing Resume...' : (analysisResults ? 'Re-analyze Resume' : 'Analyze My Resume')}
                </Button>
              ) : (
                <Button
                  color="secondary"
                  onClick={optimizeResume}
                  isLoading={isOptimizing}
                  isDisabled={!resumeText.trim() || !jobDescription.trim()}
                  startContent={<SparklesIcon className="w-4 h-4" />}
                  className="w-full"
                  size="lg"
                >
                  {isOptimizing ? 'Optimizing Resume...' : 'Optimize My Resume'}
                </Button>
              )}
            </div>
          </CardBody>
        </Card>

        {/* Results Panel */}
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">
              {activeTab === 'analyze' ? 'Analysis Results' : 'Optimization Results'}
            </h2>
          </CardHeader>
          <CardBody>
            {activeTab === 'analyze' && analysisResults ? (
              <div className="space-y-6">
                {/* Overall Score */}
                <div className="text-center">
                  <div className="text-3xl font-bold mb-2">
                    {analysisResults.overall_score}/100
                  </div>
                  <Progress
                    value={analysisResults.overall_score}
                    color={getScoreColor(analysisResults.overall_score)}
                    className="mb-2"
                  />
                  <p className="text-sm text-gray-600">Overall Resume Score</p>
                </div>

                {/* Score Breakdown */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">ATS Score</span>
                      <span className="text-sm">{analysisResults.ats_compatibility.score}/100</span>
                    </div>
                    <Progress
                      value={analysisResults.ats_compatibility.score}
                      color={getScoreColor(analysisResults.ats_compatibility.score)}
                      size="sm"
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">Content Score</span>
                      <span className="text-sm">{analysisResults.content_strength.score}/100</span>
                    </div>
                    <Progress
                      value={analysisResults.content_strength.score}
                      color={getScoreColor(analysisResults.content_strength.score)}
                      size="sm"
                    />
                  </div>
                </div>

                {/* Keywords */}
                {analysisResults.keyword_optimization.present_keywords.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2 flex items-center">
                      <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2" />
                      Found Keywords
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {analysisResults.keyword_optimization.present_keywords.slice(0, 10).map((keyword, index) => (
                        <Chip key={index} size="sm" color="success" variant="flat">
                          {keyword}
                        </Chip>
                      ))}
                    </div>
                  </div>
                )}

                {/* Missing Keywords */}
                {analysisResults.keyword_optimization.missing_keywords.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2 flex items-center">
                      <ExclamationCircleIcon className="w-4 h-4 text-orange-500 mr-2" />
                      Missing Keywords
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {analysisResults.keyword_optimization.missing_keywords.slice(0, 8).map((keyword, index) => (
                        <Chip key={index} size="sm" color="warning" variant="flat">
                          {keyword}
                        </Chip>
                      ))}
                    </div>
                  </div>
                )}

                {/* Top Suggestions */}
                {analysisResults.improvement_suggestions.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 flex items-center">
                      <LightBulbIcon className="w-4 h-4 text-blue-500 mr-2" />
                      Top Recommendations
                    </h4>
                    <div className="space-y-3">
                      {analysisResults.improvement_suggestions.slice(0, 3).map((suggestion, index) => (
                        <div key={index} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">{suggestion.category}</span>
                            <Chip size="sm" color={getPriorityColor(suggestion.priority)} variant="flat">
                              {suggestion.priority}
                            </Chip>
                          </div>
                          <p className="text-sm text-gray-700 mb-1">{suggestion.suggestion}</p>
                          {suggestion.example && (
                            <p className="text-xs text-gray-500 italic">Example: {suggestion.example}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : activeTab === 'optimize' && optimizationResult ? (
              <div className="space-y-6">
                {/* Score Improvement */}
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Score Improvement</h3>
                  <div className="flex items-center justify-between">
                    <span>Original Score: {optimizationResult.score_improvement?.original_score || 'N/A'}/100</span>
                    <span>→</span>
                    <span className="font-bold text-green-600">
                      Optimized Score: {optimizationResult.score_improvement?.optimized_score || 'N/A'}/100
                    </span>
                  </div>
                </div>

                {/* Improvements Made */}
                {optimizationResult.improvements_made && optimizationResult.improvements_made.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 flex items-center">
                      <LightBulbIcon className="w-4 h-4 text-blue-500 mr-2" />
                      Improvements Made
                    </h4>
                    <div className="space-y-3">
                      {optimizationResult.improvements_made.map((improvement: any, index: number) => (
                        <div key={index} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">{improvement.category}</span>
                          </div>
                          <p className="text-sm text-gray-700 mb-1">{improvement.change}</p>
                          <p className="text-xs text-gray-500 italic">{improvement.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Keywords Added */}
                {optimizationResult.keyword_additions && optimizationResult.keyword_additions.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2 flex items-center">
                      <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2" />
                      Keywords Added
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {optimizationResult.keyword_additions.map((keyword: string, index: number) => (
                        <Chip key={index} size="sm" color="success" variant="flat">
                          {keyword}
                        </Chip>
                      ))}
                    </div>
                  </div>
                )}

                {/* Optimized Resume Preview */}
                {optimizationResult.optimized_resume && (
                  <div>
                    <h4 className="font-medium mb-2">Optimized Resume Preview</h4>
                    <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
                      <pre className="text-sm whitespace-pre-wrap">
                        {optimizationResult.optimized_resume.substring(0, 800)}
                        {optimizationResult.optimized_resume.length > 800 ? '...' : ''}
                      </pre>
                    </div>
                    <Button
                      size="sm"
                      variant="bordered"
                      className="mt-2"
                      onClick={() => {
                        navigator.clipboard.writeText(optimizationResult.optimized_resume);
                        alert('Optimized resume copied to clipboard!');
                      }}
                    >
                      Copy Full Resume
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                {activeTab === 'analyze' ? (
                  <>
                    <ChartBarIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Upload or paste your resume to get started with AI analysis</p>
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Provide both your resume and a job description to optimize your resume</p>
                    <p className="text-sm mt-2">Job description is required for optimization</p>
                  </>
                )}
              </div>
            )}
          </CardBody>
        </Card>
      </div>

    </div>
  );
}