// Import tokenUtils from auth-api
import { tokenUtils } from './auth-api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Generic API helper
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = tokenUtils.getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add custom headers if provided
  if (options.headers) {
    Object.entries(options.headers).forEach(([key, value]) => {
      if (typeof value === 'string') {
        headers[key] = value;
      }
    });
  }

  // Skip authentication for now - TODO: Implement proper auth
  // if (token && !tokenUtils.isTokenExpired(token)) {
  //   headers.Authorization = `Bearer ${token.access_token}`;
  // }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('API Error Response:', {
      status: response.status,
      statusText: response.statusText,
      url: `${API_BASE_URL}${endpoint}`,
      errorData
    });
    throw new Error(errorData.detail || `API call failed: ${response.statusText}`);
  }

  return response.json();
}

// Job Search API
export interface JobSearchRequest {
  job_titles: string[];
  locations: string[];
  companies?: string[];
  max_results?: number;
  job_boards?: string[];
  remote_only?: boolean;
}

export interface JobPosition {
  id?: string;
  title: string;
  company: string;
  location: string;
  url: string;
  job_board: string;
  posted_date?: string;
  salary_range?: string;
  job_type?: string;
  remote_option?: string;
  description_snippet?: string;
  created_at?: string;
  updated_at?: string;
}

export interface JobSearchResponse {
  search_query: string;
  total_jobs_found: number;
  jobs: JobPosition[];
  search_timestamp: string;
  success: boolean;
  error_message?: string;
}

export const jobSearchAPI = {
  // Search for jobs
  async searchJobs(request: JobSearchRequest): Promise<JobSearchResponse> {
    return apiCall<JobSearchResponse>('/api/jobs/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get all jobs
  async getJobs(limit = 50, offset = 0, jobBoard?: string, location?: string): Promise<JobPosition[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (jobBoard) params.append('job_board', jobBoard);
    if (location) params.append('location', location);
    
    return apiCall<JobPosition[]>(`/api/jobs?${params}`);
  },

  // Get job by ID
  async getJob(jobId: string): Promise<JobPosition> {
    return apiCall<JobPosition>(`/api/jobs/${jobId}`);
  },

  // Get supported companies
  async getSupportedCompanies(): Promise<any> {
    return apiCall('/api/v2/jobs/companies');
  },

  // Get company domains
  async getCompanyDomains(): Promise<any> {
    return apiCall('/api/v2/jobs/company-domains');
  },

  // Search jobs by specific companies
  async searchJobsByCompanies(request: { job_titles: string[]; companies: string[]; locations?: string[]; max_results?: number; remote_only?: boolean }): Promise<JobSearchResponse> {
    return apiCall<JobSearchResponse>('/api/v2/jobs/search/companies', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get available scrapers
  async getAvailableScrapers(): Promise<any> {
    return apiCall('/api/v2/scrapers');
  },

  // Find similar jobs
  async findSimilarJobs(jobDescription: string, limit = 10): Promise<JobPosition[]> {
    return apiCall<JobPosition[]>('/api/jobs/similar', {
      method: 'POST',
      body: JSON.stringify({ job_description: jobDescription, limit }),
    });
  },
};

// User Profile API
export interface UserProfile {
  user: User;
  preferences?: UserPreferences;
  resumes: Resume[];
  skills: UserSkill[];
  work_experience: WorkExperience[];
  education: Education[];
  certifications: Certification[];
  application_history: ApplicationHistory[];
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  location?: string;
  timezone?: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  id: number;
  user_id: number;
  preferred_job_titles: string[];
  preferred_locations: string[];
  preferred_salary_min?: number;
  preferred_salary_max?: number;
  preferred_job_types: string[];
  remote_preference: boolean;
  notification_frequency: string;
  preferred_time: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface Resume {
  id: number;
  user_id: number;
  name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserSkill {
  id: number;
  user_id: number;
  skill_id: number;
  proficiency_level: string;
  years_of_experience?: number;
  is_highlighted: boolean;
  created_at: string;
  skill?: Skill;
}

export interface Skill {
  id: number;
  name: string;
  category?: string;
  created_at: string;
}

export interface WorkExperience {
  id: number;
  user_id: number;
  company_name: string;
  job_title: string;
  location?: string;
  start_date: string;
  end_date?: string;
  is_current: boolean;
  description?: string;
  achievements: string[];
  technologies_used: string[];
  created_at: string;
  updated_at: string;
}

export interface Education {
  id: number;
  user_id: number;
  institution_name: string;
  degree: string;
  field_of_study?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  is_current: boolean;
  gpa?: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Certification {
  id: number;
  user_id: number;
  name: string;
  issuing_organization: string;
  issue_date?: string;
  expiry_date?: string;
  credential_id?: string;
  credential_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationHistory {
  id: number;
  user_id: number;
  job_id?: string;
  resume_id?: number;
  application_date: string;
  status: string;
  notes?: string;
  follow_up_date?: string;
  created_at: string;
  updated_at: string;
}

export const userProfileAPI = {
  // Get user profile
  async getUserProfile(userId: number): Promise<UserProfile> {
    return apiCall<UserProfile>(`/api/users/${userId}/profile`);
  },

  // Get user preferences
  async getUserPreferences(userId: number): Promise<UserPreferences> {
    return apiCall<UserPreferences>(`/api/users/${userId}/preferences`);
  },

  // Create user preferences
  async createUserPreferences(userId: number, preferences: UserPreferences): Promise<UserPreferences> {
    return apiCall<UserPreferences>(`/api/users/${userId}/preferences`, {
      method: 'POST',
      body: JSON.stringify(preferences),
    });
  },

  // Update user preferences
  async updateUserPreferences(userId: number, preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    return apiCall<UserPreferences>(`/api/users/${userId}/preferences`, {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  },

  // Get user resumes
  async getUserResumes(userId: number): Promise<Resume[]> {
    return apiCall<Resume[]>(`/api/users/${userId}/resumes`);
  },

  // Upload resume
  async uploadResume(userId: number, file: File, name: string): Promise<Resume> {
    // Convert file to base64
    const arrayBuffer = await file.arrayBuffer();
    const base64Content = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
    
    const uploadRequest = {
      name: name,
      file_content: base64Content,
      file_name: file.name
    };

    return apiCall<Resume>(`/api/users/${userId}/resumes`, {
      method: 'POST',
      body: JSON.stringify(uploadRequest),
    });
  },

  // Parse resume and auto-populate profile
  async parseResume(userId: number, resumeId: number): Promise<any> {
    return apiCall(`/api/users/${userId}/resumes/${resumeId}/parse`, {
      method: 'POST',
    });
  },

  // Delete resume
  async deleteResume(userId: number, resumeId: number): Promise<void> {
    return apiCall(`/api/users/${userId}/resumes/${resumeId}`, {
      method: 'DELETE',
    });
  },

  // Get user skills
  async getUserSkills(userId: number): Promise<UserSkill[]> {
    return apiCall<UserSkill[]>(`/api/users/${userId}/skills`);
  },

  // Add skill to user
  async addUserSkill(userId: number, skillName: string, proficiencyLevel = 'intermediate', yearsOfExperience?: number): Promise<UserSkill> {
    return apiCall<UserSkill>(`/api/users/${userId}/skills`, {
      method: 'POST',
      body: JSON.stringify({
        skill_name: skillName,
        proficiency_level: proficiencyLevel,
        years_of_experience: yearsOfExperience,
      }),
    });
  },

  // Get available skills
  async getAvailableSkills(): Promise<Skill[]> {
    return apiCall<Skill[]>('/api/skills');
  },

  // Get user work experience
  async getUserWorkExperience(userId: number): Promise<WorkExperience[]> {
    return apiCall<WorkExperience[]>(`/api/users/${userId}/work-experience`);
  },

  // Add work experience
  async addWorkExperience(userId: number, workData: Omit<WorkExperience, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<WorkExperience> {
    return apiCall<WorkExperience>(`/api/users/${userId}/work-experience`, {
      method: 'POST',
      body: JSON.stringify(workData),
    });
  },

  // Get user education
  async getUserEducation(userId: number): Promise<Education[]> {
    return apiCall<Education[]>(`/api/users/${userId}/education`);
  },

  // Add education
  async addEducation(userId: number, educationData: Omit<Education, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<Education> {
    return apiCall<Education>(`/api/users/${userId}/education`, {
      method: 'POST',
      body: JSON.stringify(educationData),
    });
  },

  // Get user application history
  async getUserApplicationHistory(userId: number): Promise<ApplicationHistory[]> {
    return apiCall<ApplicationHistory[]>(`/api/users/${userId}/applications`);
  },

  // Add application history
  async addApplicationHistory(userId: number, appData: Omit<ApplicationHistory, 'id' | 'user_id' | 'application_date' | 'created_at' | 'updated_at'>): Promise<ApplicationHistory> {
    return apiCall<ApplicationHistory>(`/api/users/${userId}/applications`, {
      method: 'POST',
      body: JSON.stringify(appData),
    });
  },
};

// Job Application API
export interface JobApplicationRequest {
  user_id: number;
  form_data: Record<string, any>;
  cover_letter?: string;
  resume_file?: string;
  additional_info?: Record<string, any>;
}

export interface JobApplicationResponse {
  job_id: string;
  success: boolean;
  filled_fields: string[];
  failed_fields: string[];
  error_message?: string;
  application_timestamp?: string;
}

export const jobApplicationAPI = {
  // Apply to a job
  async applyToJob(jobId: string, request: JobApplicationRequest): Promise<JobApplicationResponse> {
    return apiCall<JobApplicationResponse>(`/api/jobs/${jobId}/apply`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Batch apply to jobs
  async batchApplyToJobs(request: { user_id: number; job_ids: string[]; form_data: Record<string, any>; max_applications?: number }): Promise<any> {
    return apiCall('/api/jobs/batch-apply', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Extract form fields
  async extractFormFields(url: string): Promise<any> {
    return apiCall('/api/forms/extract', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  },
};

// Pending Applications API
export interface PendingApplication {
  id: number;
  user_id: number;
  job_id: string;
  job_title: string;
  company_name: string;
  status: string;
  priority: string;
  form_data: Record<string, any>;
  cover_letter?: string;
  resume_id?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PendingApplicationListResponse {
  applications: PendingApplication[];
  total: number;
  limit: number;
  offset: number;
}

export const pendingApplicationAPI = {
  // Get user's pending applications
  async getUserPendingApplications(userId: number, status?: string, limit = 50, offset = 0): Promise<PendingApplicationListResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (status) params.append('status', status);
    
    return apiCall<PendingApplicationListResponse>(`/api/users/${userId}/pending-applications?${params}`);
  },

  // Get all pending applications (admin)
  async getAllPendingApplications(status?: string, limit = 50, offset = 0): Promise<PendingApplicationListResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (status) params.append('status', status);
    
    return apiCall<PendingApplicationListResponse>(`/api/pending-applications?${params}`);
  },

  // Get applications for review
  async getApplicationsForReview(limit = 50, priorityFilter?: string): Promise<PendingApplication[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });
    if (priorityFilter) params.append('priority_filter', priorityFilter);
    
    return apiCall<PendingApplication[]>(`/api/pending-applications/for-review?${params}`);
  },

  // Review pending application
  async reviewPendingApplication(applicationId: number, reviewerId: number, reviewData: { action: string; notes?: string }): Promise<any> {
    return apiCall(`/api/pending-applications/${applicationId}/review`, {
      method: 'POST',
      body: JSON.stringify({
        reviewer_id: reviewerId,
        ...reviewData,
      }),
    });
  },

  // Cancel pending application
  async cancelPendingApplication(applicationId: number, userId: number): Promise<any> {
    return apiCall(`/api/pending-applications/${applicationId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  },
};

// Analytics API
export interface SearchStatistics {
  total_searches: number;
  total_jobs_found: number;
  average_jobs_per_search: number;
  most_searched_titles: Array<{ title: string; count: number }>;
  most_searched_locations: Array<{ location: string; count: number }>;
  search_timeline: Array<{ date: string; searches: number; jobs_found: number }>;
}

export interface ApplicationStatistics {
  total_applications: number;
  successful_applications: number;
  failed_applications: number;
  success_rate: number;
  average_application_time: number;
  most_applied_companies: Array<{ company: string; applications: number }>;
  application_timeline: Array<{ date: string; applications: number; successful: number }>;
}

export const analyticsAPI = {
  // Get search statistics
  async getSearchStatistics(): Promise<SearchStatistics> {
    return apiCall<SearchStatistics>('/api/analytics/search-stats');
  },

  // Get application statistics
  async getApplicationStatistics(): Promise<ApplicationStatistics> {
    return apiCall<ApplicationStatistics>('/api/analytics/application-stats');
  },
};

// Job Recommendations API
export interface JobMatchRequest {
  user_id: number;
  job_description: string;
  limit?: number;
}

export interface JobMatchResponse {
  job_id: string;
  title: string;
  company: string;
  match_score: number;
  match_reasons: string[];
  skills_match: string[];
  experience_match: boolean;
}

export const recommendationsAPI = {
  // Get job recommendations for user
  async getJobRecommendations(userId: number, limit = 10, jobBoard?: string): Promise<JobPosition[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });
    if (jobBoard) params.append('job_board', jobBoard);
    
    return apiCall<JobPosition[]>(`/api/users/${userId}/job-recommendations?${params}`);
  },

  // Match jobs for user
  async matchJobsForUser(userId: number, jobDescription: string, limit = 5): Promise<JobMatchResponse[]> {
    return apiCall<JobMatchResponse[]>(`/api/users/${userId}/match-jobs`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        job_description: jobDescription,
        limit,
      }),
    });
  },
};

// Digest API
export interface GenerateDigestRequest {
  user_id: number;
  digest_type: string;
  custom_date?: string;
}

export interface DigestResponse {
  success: boolean;
  digest_content?: string;
  error_message?: string;
  generated_at: string;
}

export const digestAPI = {
  // Generate digest
  async generateDigest(request: GenerateDigestRequest): Promise<DigestResponse> {
    return apiCall<DigestResponse>('/api/v1/digest/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get digest preferences
  async getDigestPreferences(userId: number): Promise<any> {
    return apiCall(`/api/v1/digest/preferences/${userId}`);
  },

  // Update digest preferences
  async updateDigestPreferences(userId: number, preferences: any): Promise<any> {
    return apiCall(`/api/v1/digest/preferences/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  },
};

// Cache API
export interface CacheStats {
  total_files: number;
  total_size_mb: number;
  expired_files: number;
  cache_duration_hours: number;
}

export interface CacheInfo {
  cache_stats: CacheStats;
  cache_location: string;
  cache_duration_hours: number;
  description: string;
}

export const cacheAPI = {
  // Get cache statistics
  async getCacheStats(): Promise<CacheStats> {
    return apiCall<CacheStats>('/api/v2/jobs/cache/stats');
  },

  // Clear cache
  async clearCache(): Promise<{ message: string }> {
    return apiCall<{ message: string }>('/api/v2/jobs/cache/clear', {
      method: 'DELETE',
    });
  },

  // Get detailed cache information
  async getCacheInfo(): Promise<CacheInfo> {
    return apiCall<CacheInfo>('/api/v2/jobs/cache/info');
  },
};

// Chatbot API
export interface ChatMessage {
  id: string;
  conversation_id: string;
  message_type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: any;
}

export interface ChatConversation {
  conversation_id: string;
  title: string;
  status: 'active' | 'ended';
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
  message_count?: number;
}

export interface StartConversationRequest {
  user_id: number;
  conversation_type: 'general' | 'job_search' | 'resume_review' | 'interview_prep' | 'career_guidance';
}

export interface StartConversationResponse {
  conversation_id: string;
  status: string;
  conversation: ChatConversation;
}

export interface SendMessageRequest {
  user_id: number;
  message: string;
}

export interface SendMessageResponse {
  message_id: string;
  content: string;
  timestamp: string;
  conversation_id: string;
}

export interface ChatbotStats {
  total_conversations: number;
  active_conversations: number;
  total_messages: number;
  rate_limit_remaining: number;
}

export interface UserConversationsResponse {
  conversations: ChatConversation[];
  total: number;
}

export const chatbotAPI = {
  // Start a new conversation
  async startConversation(request: StartConversationRequest): Promise<StartConversationResponse> {
    return apiCall<StartConversationResponse>('/api/chatbot/start', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Send a message to a conversation
  async sendMessage(conversationId: string, request: SendMessageRequest): Promise<SendMessageResponse> {
    return apiCall<SendMessageResponse>(`/api/chatbot/${conversationId}/message`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get conversation history
  async getConversationHistory(conversationId: string, userId: number): Promise<ChatConversation> {
    return apiCall<ChatConversation>(`/api/chatbot/${conversationId}/history?user_id=${userId}`);
  },

  // End a conversation
  async endConversation(conversationId: string, userId: number): Promise<{ conversation_id: string; status: string; success: boolean }> {
    return apiCall<{ conversation_id: string; status: string; success: boolean }>(`/api/chatbot/${conversationId}/end?user_id=${userId}`, {
      method: 'POST',
    });
  },

  // Get user's conversations
  async getUserConversations(userId: number): Promise<UserConversationsResponse> {
    return apiCall<UserConversationsResponse>(`/api/users/${userId}/chatbot/conversations`);
  },

  // Get user's chatbot statistics
  async getUserStats(userId: number): Promise<ChatbotStats> {
    return apiCall<ChatbotStats>(`/api/users/${userId}/chatbot/stats`);
  },
}; 

export const resumeReviewAPI = {
  async uploadAndAnalyzeResume(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE_URL}/api/resume/review`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Resume analysis failed');
    }
    return response.json();
  },

  async downloadImprovedResume(file: File): Promise<Blob> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE_URL}/api/resume/improve`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      throw new Error('Failed to generate improved resume');
    }
    return response.blob();
  }
}; 