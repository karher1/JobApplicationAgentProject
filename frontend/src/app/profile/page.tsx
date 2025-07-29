'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from "@heroui/react";
import { userProfileAPI, UserProfile, UserPreferences, Resume, UserSkill, WorkExperience, Education } from '@/lib/api';
import { tokenUtils } from '@/lib/auth-api';

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [editing, setEditing] = useState<boolean | string>(false);
  const [preferences, setPreferences] = useState<Partial<UserPreferences>>({});
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [jobTitlesInput, setJobTitlesInput] = useState('');
  const [locationsInput, setLocationsInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const router = useRouter();

  useEffect(() => {
    // Check authentication and get user ID
    const token = tokenUtils.getToken();
    console.log('Token from localStorage:', token);
    
    if (!token || tokenUtils.isTokenExpired(token)) {
      router.push('/login');
      return;
    }
    
    console.log('User ID from token:', token.user_id, 'Type:', typeof token.user_id);
    setUserId(token.user_id);
    loadUserProfile(token.user_id);
  }, [router]);

  const loadUserProfile = async (userIdToLoad: number) => {
    try {
      const userProfile = await userProfileAPI.getUserProfile(userIdToLoad);
      setProfile(userProfile);
      if (userProfile.preferences) {
        setPreferences(userProfile.preferences);
        setJobTitlesInput(userProfile.preferences.preferred_job_titles?.join(', ') || '');
        setLocationsInput(userProfile.preferences.preferred_locations?.join(', ') || '');
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const sanitizeFileName = (fileName: string): string => {
    // Remove file extension and sanitize the name
    const nameWithoutExtension = fileName.replace(/\.[^/.]+$/, '');
    // Replace special characters with underscores and limit length
    const sanitized = nameWithoutExtension
      .replace(/[^a-zA-Z0-9\s\-_]/g, '_')
      .replace(/\s+/g, '_')
      .substring(0, 100);
    return sanitized || 'resume';
  };

  const handleUploadResume = async () => {
    if (!selectedFile || !userId) return;

    try {
      console.log('Uploading resume for userId:', userId, 'Type:', typeof userId);
      console.log('Resume details:', selectedFile.name, 'Size:', selectedFile.size, 'Type:', selectedFile.type);
      
      // Sanitize the file name for display
      const sanitizedName = sanitizeFileName(selectedFile.name);
      
      const resume = await userProfileAPI.uploadResume(userId, selectedFile, sanitizedName);
      console.log('Resume uploaded successfully:', resume);
      // Refresh profile to show new resume
      await loadUserProfile(userId);
      setSelectedFile(null);
      setSaveMessage('Resume uploaded successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Error uploading resume:', error);
      setSaveMessage(`Error uploading resume: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setTimeout(() => setSaveMessage(''), 5000);
    }
  };

  const handleParseResume = async (resumeId: number) => {
    if (!userId) return;

    try {
      setSaving(true);
      setSaveMessage('Parsing resume and auto-filling profile...');
      
      const result = await userProfileAPI.parseResume(userId, resumeId);
      console.log('Resume parsing result:', result);
      
      if (result.success) {
        const populationResult = result.population_result;
        setSaveMessage(`Resume parsed successfully! Added ${populationResult.skills_added} skills, ${populationResult.work_experience_added} work experiences, and ${populationResult.education_added} education entries.`);
        
        // Refresh profile to show new data
        await loadUserProfile(userId);
      } else {
        setSaveMessage('Failed to parse resume. Please try again.');
      }
      
      setTimeout(() => setSaveMessage(''), 5000);
    } catch (error) {
      console.error('Error parsing resume:', error);
      setSaveMessage(`Error parsing resume: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setTimeout(() => setSaveMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteResume = async (resumeId: number, resumeName: string) => {
    if (!userId) return;
    
    // Confirm deletion
    if (!confirm(`Are you sure you want to delete "${resumeName}"? This action cannot be undone.`)) {
      return;
    }
    
    try {
      setSaving(true);
      setSaveMessage('Deleting resume...');
      
      await userProfileAPI.deleteResume(userId, resumeId);
      
      // Refresh profile to show updated list
      await loadUserProfile(userId);
      
      setSaveMessage('Resume deleted successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Error deleting resume:', error);
      setSaveMessage(`Error deleting resume: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setTimeout(() => setSaveMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveSkill = async (skillId: number) => {
    // TODO: Implement skill removal
    console.log('Remove skill:', skillId);
    setSaveMessage('Skill removal functionality coming soon!');
    setTimeout(() => setSaveMessage(''), 3000);
  };

  const handleRemoveExperience = async (expId: number) => {
    if (!userId) return;
    
    try {
      setSaving(true);
      setSaveMessage('Deleting work experience...');
      
      await userProfileAPI.deleteWorkExperience(userId, expId);
      
      // Refresh profile to show updated data
      await loadUserProfile(userId);
      
      setSaveMessage('Work experience deleted successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Error deleting work experience:', error);
      setSaveMessage(`Error deleting work experience: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setTimeout(() => setSaveMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveEducation = async (eduId: number) => {
    // TODO: Implement education removal
    console.log('Remove education:', eduId);
    setSaveMessage('Education removal functionality coming soon!');
    setTimeout(() => setSaveMessage(''), 3000);
  };

  const handleUpdatePreferences = async () => {
    if (!userId) return;
    
    setSaving(true);
    setSaveMessage('');
    
    try {
      // Process the input strings when saving
      const updatedPreferences = {
        ...preferences,
        preferred_job_titles: jobTitlesInput.split(',').map(s => s.trim()).filter(s => s.length > 0),
        preferred_locations: locationsInput.split(',').map(s => s.trim()).filter(s => s.length > 0)
      };
      
      try {
        // Try to update first
        await userProfileAPI.updateUserPreferences(userId, updatedPreferences);
      } catch (updateError: unknown) {
        // If update fails (404), try to create preferences
        const errorMessage = updateError instanceof Error ? updateError.message : '';
        if (errorMessage.includes('404') || errorMessage.includes('not found')) {
          console.log('Preferences not found, creating new preferences...');
          await userProfileAPI.createUserPreferences(userId, {
            ...updatedPreferences,
            user_id: userId,
            preferred_job_types: [],
            notification_frequency: "daily",
            preferred_time: "09:00:00",
            timezone: "UTC",
            id: 0, // Will be set by the backend
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          } as UserPreferences);
        } else {
          throw updateError;
        }
      }
      
      setEditing(false);
      setSaveMessage('Preferences saved successfully!');
      await loadUserProfile(userId);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Error saving preferences:', error);
      setSaveMessage('Error saving preferences. Please try again.');
      setTimeout(() => setSaveMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  const calculateProfileCompletion = (profile: UserProfile | null): number => {
    if (!profile) return 0;
    
    let completed = 0;
    let total = 0;
    
    // Basic profile information (30% weight)
    total += 6;
    if (profile.user.first_name) completed++;
    if (profile.user.last_name) completed++;
    if (profile.user.email) completed++;
    if (profile.user.phone) completed++;
    if (profile.user.linkedin_url) completed++;
    if (profile.user.location) completed++;
    
    // Resume (20% weight)
    total += 4;
    if (profile.resumes && profile.resumes.length > 0) completed += 4;
    
    // Skills (15% weight)
    total += 3;
    if (profile.skills && profile.skills.length >= 3) completed += 3;
    else if (profile.skills && profile.skills.length > 0) completed += Math.floor(profile.skills.length);
    
    // Work Experience (15% weight)
    total += 3;
    if (profile.work_experience && profile.work_experience.length >= 2) completed += 3;
    else if (profile.work_experience && profile.work_experience.length > 0) completed += Math.floor(profile.work_experience.length * 1.5);
    
    // Education (10% weight)
    total += 2;
    if (profile.education && profile.education.length > 0) completed += 2;
    
    // Preferences (10% weight)
    total += 2;
    if (profile.preferences?.preferred_job_titles && profile.preferences.preferred_job_titles.length > 0) completed++;
    if (profile.preferences?.preferred_salary_min && profile.preferences?.preferred_salary_max) completed++;
    
    return Math.round((completed / total) * 100);
  };

  const getProfileCompletionMessage = (percentage: number): string => {
    if (percentage >= 90) return "Your profile is complete! 🎉";
    if (percentage >= 70) return "Almost done! Add a few more details.";
    if (percentage >= 50) return "You're halfway there! Keep going.";
    if (percentage >= 25) return "Good start! Add more information to get better matches.";
    return "Let's build your profile to find great opportunities!";
  };

  const formatDate = (dateInput: string | Date | null | undefined) => {
    if (!dateInput) return '';
    
    try {
      const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(date.getTime())) return '';
      return date.toLocaleDateString();
    } catch (error) {
      return '';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">Profile not found</p>
          </div>
        </Card>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'preferences', label: 'Preferences' },
    { id: 'resumes', label: 'Resumes' },
    { id: 'skills', label: 'Skills' },
    { id: 'experience', label: 'Experience' },
    { id: 'education', label: 'Education' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
            Profile
          </h1>
          <p className="text-gray-300 text-lg">
            Manage your professional profile and preferences
          </p>
        </div>

        {/* Profile Overview */}
        <Card className="mb-6 bg-white/5 backdrop-blur-sm border border-white/10">
          <div className="p-6">
            <div className="flex items-center gap-6 mb-6">
              <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                {profile.user.first_name[0]}{profile.user.last_name[0]}
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-white">
                  {profile.user.first_name} {profile.user.last_name}
                </h2>
                <p className="text-gray-300">{profile.user.email}</p>
                {profile.user.location && (
                  <p className="text-gray-400">{profile.user.location}</p>
                )}
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex gap-2 mb-6 overflow-x-auto">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-white/10 text-gray-300 hover:bg-white/20'
                  }`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </Card>

        {/* Tab Content */}
        <div className="space-y-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Profile Completion Card */}
              <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 backdrop-blur-sm border border-purple-500/20">
                <div className="p-6">
                  {(() => {
                    const completionPercentage = calculateProfileCompletion(profile);
                    const message = getProfileCompletionMessage(completionPercentage);
                    return (
                      <>
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold text-white">Profile Completion</h3>
                          <span className="text-2xl font-bold text-white">{completionPercentage}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-3 mb-3">
                          <div 
                            className={`h-3 rounded-full transition-all duration-500 ${
                              completionPercentage >= 90 ? 'bg-green-500' :
                              completionPercentage >= 70 ? 'bg-blue-500' :
                              completionPercentage >= 50 ? 'bg-yellow-500' :
                              'bg-orange-500'
                            }`}
                            style={{ width: `${completionPercentage}%` }}
                          ></div>
                        </div>
                        <p className="text-gray-300 text-sm">{message}</p>
                        {completionPercentage < 90 && (
                          <div className="mt-3 text-xs text-gray-400">
                            <p>💡 <strong>Tips to improve:</strong></p>
                            <ul className="list-disc list-inside mt-1 space-y-1">
                              {!profile?.user.phone && <li>Add your phone number</li>}
                              {!profile?.user.linkedin_url && <li>Add your LinkedIn profile</li>}
                              {!profile?.user.location && <li>Add your location</li>}
                              {(!profile?.resumes || profile.resumes.length === 0) && <li>Upload your resume</li>}
                              {(!profile?.skills || profile.skills.length < 3) && <li>Add at least 3 skills</li>}
                              {(!profile?.work_experience || profile.work_experience.length === 0) && <li>Add work experience</li>}
                              {(!profile?.education || profile.education.length === 0) && <li>Add education details</li>}
                              {(!profile?.preferences?.preferred_job_titles || profile.preferences.preferred_job_titles.length === 0) && <li>Set job preferences</li>}
                            </ul>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              </Card>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Contact Info</h3>
                  <div className="space-y-2">
                    <p className="text-gray-300"><strong>Email:</strong> {profile.user.email}</p>
                    {profile.user.phone && (
                      <p className="text-gray-300"><strong>Phone:</strong> {profile.user.phone}</p>
                    )}
                    {profile.user.location && (
                      <p className="text-gray-300"><strong>Location:</strong> {profile.user.location}</p>
                    )}
                  </div>
                </div>
              </Card>

              <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Resumes</h3>
                  <p className="text-gray-300">{profile.resumes.length} resume(s) uploaded</p>
                  {profile.resumes.filter(r => r.is_primary).length > 0 && (
                    <span className="inline-block px-2 py-1 bg-green-500 text-white text-xs rounded mt-2">Primary Resume Set</span>
                  )}
                </div>
              </Card>

              <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Skills</h3>
                  <p className="text-gray-300">{profile.skills.length} skills listed</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {profile.skills.slice(0, 5).map((skill) => (
                      <span key={skill.id} className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded border border-blue-500/30">
                        {skill.skill?.name || 'Unknown'}
                      </span>
                    ))}
                    {profile.skills.length > 5 && (
                      <span className="px-2 py-1 bg-gray-500/20 text-gray-300 text-xs rounded border border-gray-500/30">
                        +{profile.skills.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
              </Card>
            </div>
            </div>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-semibold text-white">Job Preferences</h3>
                  <button
                    onClick={() => setEditing(!editing)}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    {editing ? 'Cancel' : 'Edit'}
                  </button>
                </div>

                {editing ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-gray-300 mb-2">Preferred Job Titles</label>
                      <input
                        type="text"
                        value={jobTitlesInput}
                        onChange={(e) => setJobTitlesInput(e.target.value)}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                        placeholder="Software Engineer, QA Engineer, etc."
                      />
                    </div>
                    <div>
                      <label className="block text-gray-300 mb-2">Preferred Locations</label>
                      <input
                        type="text"
                        value={locationsInput}
                        onChange={(e) => setLocationsInput(e.target.value)}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                        placeholder="San Francisco, Remote, etc."
                      />
                    </div>
                                         <div>
                       <label className="block text-gray-300 mb-2">Minimum Salary</label>
                       <input
                         type="number"
                         value={preferences.preferred_salary_min || ''}
                         onChange={(e) => setPreferences({
                           ...preferences,
                           preferred_salary_min: parseInt(e.target.value) || undefined
                         })}
                         className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                         placeholder="80000"
                       />
                     </div>
                     <div>
                       <label className="block text-gray-300 mb-2">Maximum Salary</label>
                       <input
                         type="number"
                         value={preferences.preferred_salary_max || ''}
                         onChange={(e) => setPreferences({
                           ...preferences,
                           preferred_salary_max: parseInt(e.target.value) || undefined
                         })}
                         className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                         placeholder="120000"
                       />
                     </div>
                     <div>
                       <label className="block text-gray-300 mb-2">Remote Preference</label>
                       <div className="flex items-center gap-4">
                         <label className="flex items-center">
                           <input
                             type="checkbox"
                             checked={preferences.remote_preference || false}
                             onChange={(e) => setPreferences({
                               ...preferences,
                               remote_preference: e.target.checked
                             })}
                             className="mr-2"
                           />
                           <span className="text-white">Prefer remote work</span>
                         </label>
                       </div>
                     </div>
                    <button
                      onClick={handleUpdatePreferences}
                      disabled={saving}
                      className={`px-6 py-2 text-white rounded-lg transition-colors ${
                        saving 
                          ? 'bg-gray-500 cursor-not-allowed' 
                          : 'bg-green-500 hover:bg-green-600'
                      }`}
                    >
                      {saving ? 'Saving...' : 'Save Preferences'}
                    </button>
                    
                    {/* Save Status Message */}
                    {saveMessage && (
                      <div className={`mt-4 p-3 rounded-lg ${
                        saveMessage.includes('Error') 
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
                          : 'bg-green-500/20 text-green-400 border border-green-500/30'
                      }`}>
                        {saveMessage}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <strong className="text-gray-300">Preferred Job Titles:</strong>
                      <p className="text-white">{preferences.preferred_job_titles?.join(', ') || 'Not set'}</p>
                    </div>
                    <div>
                      <strong className="text-gray-300">Preferred Locations:</strong>
                      <p className="text-white">{preferences.preferred_locations?.join(', ') || 'Not set'}</p>
                    </div>
                                         <div>
                       <strong className="text-gray-300">Salary Range:</strong>
                       <p className="text-white">
                         {preferences.preferred_salary_min && preferences.preferred_salary_max 
                           ? `$${preferences.preferred_salary_min.toLocaleString()} - $${preferences.preferred_salary_max.toLocaleString()}`
                           : 'Not set'
                         }
                       </p>
                     </div>
                     <div>
                       <strong className="text-gray-300">Remote Preference:</strong>
                       <p className="text-white">{preferences.remote_preference ? 'Remote preferred' : 'No preference'}</p>
                     </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Resumes Tab */}
          {activeTab === 'resumes' && (
            <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Resume Management</h3>
                
                {/* Upload Section */}
                <div className="mb-6 p-4 border border-white/20 rounded-lg">
                  <h4 className="text-white font-medium mb-2">Upload New Resume</h4>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileChange}
                    className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-500 file:text-white hover:file:bg-blue-600"
                  />
                  {selectedFile && (
                    <button
                      onClick={handleUploadResume}
                      className="mt-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                    >
                      Upload Resume
                    </button>
                  )}
                  
                  {/* Upload Status Message */}
                  {saveMessage && activeTab === 'resumes' && (
                    <div className={`mt-4 p-3 rounded-lg ${
                      saveMessage.includes('Error') 
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
                        : 'bg-green-500/20 text-green-400 border border-green-500/30'
                    }`}>
                      {saveMessage}
                    </div>
                  )}
                </div>

                {/* Resume List */}
                <div className="space-y-3">
                  {profile.resumes.map((resume) => (
                    <div key={resume.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium truncate" title={resume.name}>
                          {resume.name}
                        </p>
                        <p className="text-gray-400 text-sm">
                          Uploaded: {formatDate(resume.created_at)}
                          {resume.file_size && (
                            <span className="ml-2">
                              ({Math.round(resume.file_size / 1024)} KB)
                            </span>
                          )}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {resume.is_primary && (
                          <span className="px-2 py-1 bg-green-500 text-white text-xs rounded">Primary</span>
                        )}
                        <button 
                          onClick={() => handleParseResume(resume.id)}
                          className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600 mr-2"
                        >
                          Parse & Auto-fill
                        </button>
                        <button className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 mr-2">
                          Download
                        </button>
                        <button 
                          onClick={() => handleDeleteResume(resume.id, resume.name)}
                          className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {/* Skills Tab */}
          {activeTab === 'skills' && (
            <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-white">Skills</h3>
                  <button
                    onClick={() => setEditing(!editing)}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    {editing ? 'Done' : 'Edit Skills'}
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((skill) => (
                    <div key={skill.id} className="relative group">
                      <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded border border-blue-500/30 flex items-center">
                        {skill.skill?.name || 'Unknown'}
                        {editing && (
                          <button
                            onClick={() => handleRemoveSkill(skill.id)}
                            className="ml-2 text-red-400 hover:text-red-300"
                          >
                            ×
                          </button>
                        )}
                      </span>
                    </div>
                  ))}
                  {editing && (
                    <button
                      onClick={() => setEditing('add-skill')}
                      className="px-3 py-1 bg-green-500/20 text-green-300 rounded border border-green-500/30 hover:bg-green-500/30"
                    >
                      + Add Skill
                    </button>
                  )}
                </div>
                {editing === 'add-skill' && (
                  <div className="mt-4 p-4 bg-white/5 rounded-lg">
                    <input
                      type="text"
                      placeholder="Skill name"
                      className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 mb-2"
                    />
                    <div className="flex gap-2">
                      <button className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600">
                        Add
                      </button>
                      <button 
                        onClick={() => setEditing(false)}
                        className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Experience Tab */}
          {activeTab === 'experience' && (
            <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-white">Work Experience</h3>
                  <button
                    onClick={() => setEditing(!editing)}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    {editing ? 'Done' : 'Edit Experience'}
                  </button>
                </div>
                <div className="space-y-4">
                  {profile.work_experience.map((exp) => (
                    <div key={exp.id} className="p-4 bg-white/5 rounded-lg relative">
                      {editing && (
                        <button
                          onClick={() => handleRemoveExperience(exp.id)}
                          className="absolute top-2 right-2 text-red-400 hover:text-red-300 text-xl"
                        >
                          ×
                        </button>
                      )}
                      <h4 className="text-white font-medium">{exp.job_title}</h4>
                      <p className="text-blue-300">{exp.company_name}</p>
                      <p className="text-gray-400 text-sm">
                        {exp.start_date ? formatDate(exp.start_date) : ''} - {exp.end_date ? formatDate(exp.end_date) : 'Present'}
                      </p>
                      <p className="text-gray-300 mt-2">{exp.description}</p>
                    </div>
                  ))}
                  {editing && (
                    <button
                      onClick={() => setEditing('add-experience')}
                      className="w-full p-4 bg-green-500/20 text-green-300 rounded-lg border border-green-500/30 hover:bg-green-500/30 transition-colors"
                    >
                      + Add Work Experience
                    </button>
                  )}
                </div>
              </div>
            </Card>
          )}

          {/* Education Tab */}
          {activeTab === 'education' && (
            <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-white">Education</h3>
                  <button
                    onClick={() => setEditing(!editing)}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    {editing ? 'Done' : 'Edit Education'}
                  </button>
                </div>
                <div className="space-y-4">
                  {profile.education.map((edu) => (
                    <div key={edu.id} className="p-4 bg-white/5 rounded-lg relative">
                      {editing && (
                        <button
                          onClick={() => handleRemoveEducation(edu.id)}
                          className="absolute top-2 right-2 text-red-400 hover:text-red-300 text-xl"
                        >
                          ×
                        </button>
                      )}
                      <h4 className="text-white font-medium">{edu.degree}</h4>
                      <p className="text-blue-300">{edu.institution_name}</p>
                      <p className="text-gray-400 text-sm">
                        {edu.start_date ? formatDate(edu.start_date) : ''} - {edu.end_date ? formatDate(edu.end_date) : 'Present'}
                      </p>
                      {edu.gpa && (
                        <p className="text-gray-300">GPA: {edu.gpa}</p>
                      )}
                    </div>
                  ))}
                  {editing && (
                    <button
                      onClick={() => setEditing('add-education')}
                      className="w-full p-4 bg-green-500/20 text-green-300 rounded-lg border border-green-500/30 hover:bg-green-500/30 transition-colors"
                    >
                      + Add Education
                    </button>
                  )}
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
} 