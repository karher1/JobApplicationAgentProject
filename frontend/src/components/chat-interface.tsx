'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  Card, 
  CardBody, 
  Button, 
  Input, 
  Select, 
  SelectItem, 
  Chip, 
  Avatar, 
  Spinner,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure
} from '@heroui/react';
import { 
  Send, 
  MessageCircle, 
  Bot, 
  User, 
  Settings,
  CheckCircle,
  XCircle,
  Search,
  FileText
} from 'lucide-react';
import { 
  chatbotAPI, 
  ChatMessage, 
  ChatConversation, 
  StartConversationRequest, 
  ChatbotStats,
  resumeReviewAPI
} from '@/lib/api';

interface ChatInterfaceProps {
  userId: number;
  initialConversationType?: 'general' | 'job_search' | 'resume_review' | 'interview_prep' | 'career_guidance';
}

export default function ChatInterface({ userId, initialConversationType = 'general' }: ChatInterfaceProps) {
  const [conversation, setConversation] = useState<ChatConversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [conversationType, setConversationType] = useState(initialConversationType);
  const [stats, setStats] = useState<ChatbotStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedResume, setSelectedResume] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [lastUploadedFile, setLastUploadedFile] = useState<File | null>(null);
  const [improvedResumeContent, setImprovedResumeContent] = useState<string | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [typingText, setTypingText] = useState('');
  const [isDisplayingTyping, setIsDisplayingTyping] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Load user stats on mount
  useEffect(() => {
    loadUserStats();
  }, [userId]);

  const loadUserStats = async () => {
    try {
      const userStats = await chatbotAPI.getUserStats(userId);
      setStats(userStats);
    } catch (error) {
      console.error('Error loading user stats:', error);
    }
  };

  const startNewConversation = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const request: StartConversationRequest = {
        user_id: userId,
        conversation_type: conversationType,
      };
      
      const response = await chatbotAPI.startConversation(request);
      setConversation(response.conversation);
      setMessages(response.conversation.messages);
      await loadUserStats();
    } catch (error) {
      console.error('Error starting conversation:', error);
      setError('Failed to start conversation. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !conversation || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsTyping(true);
    setError(null);

    // Add user message immediately to UI
    const tempUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      conversation_id: conversation.conversation_id,
      message_type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      const response = await chatbotAPI.sendMessage(conversation.conversation_id, {
        user_id: userId,
        message: userMessage,
      });

      // Replace temp message with real message and add AI response
      const aiMessage: ChatMessage = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        message_type: 'assistant',
        content: response.content,
        timestamp: response.timestamp,
      };

      setMessages(prev => {
        const filteredMessages = prev.filter(msg => msg.id !== tempUserMessage.id);
        return [...filteredMessages, 
          { ...tempUserMessage, id: `user-${Date.now()}` }, 
          aiMessage
        ];
      });

      // Start typing animation for AI response
      await typeText(response.content);

      await loadUserStats();
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      // Remove temp message on error
      setMessages(prev => prev.filter(msg => msg.id !== tempUserMessage.id));
    } finally {
      setIsTyping(false);
    }
  };

  const endConversation = async () => {
    if (!conversation) return;

    try {
      await chatbotAPI.endConversation(conversation.conversation_id, userId);
      setConversation(null);
      setMessages([]);
      await loadUserStats();
      onClose();
    } catch (error) {
      console.error('Error ending conversation:', error);
      setError('Failed to end conversation.');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getConversationTypeColor = (type: string) => {
    switch (type) {
      case 'job_search': return 'primary';
      case 'resume_review': return 'secondary';
      case 'interview_prep': return 'success';
      case 'career_guidance': return 'warning';
      default: return 'default';
    }
  };

  const getConversationTypeLabel = (type: string) => {
    switch (type) {
      case 'job_search': return 'Job Search';
      case 'resume_review': return 'Resume Review';
      case 'interview_prep': return 'Interview Prep';
      case 'career_guidance': return 'Career Guidance';
      default: return 'General Chat';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessageContent = (content: string) => {
    // Split content by markdown links and render them as clickable links
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(content)) !== null) {
      // Add text before the link
      if (match.index > lastIndex) {
        parts.push(content.slice(lastIndex, match.index));
      }
      
      // Add the clickable link
      parts.push(
        <a
          key={match.index}
          href={match[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 underline"
        >
          {match[1]}
        </a>
      );
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(content.slice(lastIndex));
    }
    
    return parts.length > 1 ? parts : content;
  };

  const typeText = async (text: string) => {
    setIsDisplayingTyping(true);
    setTypingText('');
    
    for (let i = 0; i <= text.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 20)); // Typing speed
      setTypingText(text.slice(0, i));
    }
    
    setIsDisplayingTyping(false);
  };

  const triggerConfetti = () => {
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 3000);
  };

  const ConfettiEffect = () => {
    if (!showConfetti) return null;
    
    return (
      <div className="fixed inset-0 pointer-events-none z-50">
        {Array.from({ length: 50 }).map((_, i) => (
          <div
            key={i}
            className="absolute animate-bounce"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${1 + Math.random() * 2}s`
            }}
          >
            <div
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444'][Math.floor(Math.random() * 5)]
              }}
            />
          </div>
        ))}
      </div>
    );
  };

  // Placeholder for resume upload/analysis
  const handleResumeUpload = async () => {
    if (!selectedResume) return;
    setIsUploading(true);
    setError(null);
    try {
      const result = await resumeReviewAPI.uploadAndAnalyzeResume(selectedResume);
      setIsUploading(false);
      setLastUploadedFile(selectedResume); // Save for download
      setSelectedResume(null);
      if (result && result.success && result.analysis) {
        const { 
          skills, 
          ats_keywords, 
          comprehensive_analysis, 
          improvement_suggestions, 
          ats_analysis,
          improved_resume 
        } = result.analysis;
        
        // Store improved resume content for preview
        setImprovedResumeContent(improved_resume);
        
        // Trigger confetti for successful upload
        triggerConfetti();
        
        const feedback = `📋 Resume Analysis Complete!

🎯 Skills Detected:
${skills.join(', ')}

🔍 ATS Keywords:
${ats_keywords.join(', ')}

📊 Comprehensive Analysis:
${comprehensive_analysis}

💡 Improvement Suggestions:
${improvement_suggestions}

🤖 ATS Compatibility Analysis:
${ats_analysis}

✨ Your Improved Resume:
${improved_resume}

💡 Tip: Use the improved version above as a template to enhance your original resume!`;

        setMessages(prev => [...prev, {
          id: `resume-feedback-${Date.now()}`,
          conversation_id: conversation?.conversation_id || 'resume-review',
          message_type: 'assistant',
          content: feedback,
          timestamp: new Date().toISOString(),
        }]);
        
        // Add view/download options message
        setMessages(prev => [...prev, {
          id: `view-download-option-${Date.now()}`,
          conversation_id: conversation?.conversation_id || 'resume-review',
          message_type: 'assistant',
          content: `🎯 Your Improved Resume is Ready!

• 👀 View: Preview your improved resume before downloading
• 📥 Download: Get the improved version as a text file

Use the buttons below to view or download your optimized resume!`,
          timestamp: new Date().toISOString(),
        }]);
      } else {
        setError('Resume analysis failed. Please try again.');
      }
    } catch (err: unknown) {
      setIsUploading(false);
      setError(err instanceof Error ? err.message : 'Resume analysis failed.');
    }
  };

  const handleDownloadImprovedResume = async () => {
    if (!lastUploadedFile) return;
    setIsUploading(true);
    setError(null);
    try {
      const blob = await resumeReviewAPI.downloadImprovedResume(lastUploadedFile);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `improved_${lastUploadedFile.name.replace(/\.[^/.]+$/, "")}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setIsUploading(false);
    } catch (err: unknown) {
      setIsUploading(false);
      setError(err instanceof Error ? err.message : 'Download failed.');
    }
  };

  return (
    <div className="flex flex-col h-full bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-black/30 backdrop-blur-sm border-b border-white/10">
        <div className="flex items-center gap-3">
          <Avatar
            icon={<Bot className="w-5 h-5" />}
            className="bg-gradient-to-r from-blue-500 to-purple-500"
          />
          <div>
            <h2 className="text-base font-semibold text-white">Chat Assistant</h2>
            <div className="flex items-center gap-2">
              <Chip
                color={getConversationTypeColor(conversationType)}
                size="sm"
                variant="flat"
              >
                {getConversationTypeLabel(conversationType)}
              </Chip>
              {conversation && (
                <span className="text-xs text-gray-400">
                  {conversation.status === 'active' ? 'Active' : 'Ended'}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {stats && (
            <div className="hidden sm:flex items-center gap-3 text-sm text-gray-400">
              <span>{stats.active_conversations} active</span>
              <span>{stats.rate_limit_remaining} calls left</span>
            </div>
          )}
          
          <Button
            isIconOnly
            variant="light"
            size="sm"
            onPress={onOpen}
            className="text-gray-400 hover:text-white"
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {!conversation ? (
          // Welcome Screen
          <div className="flex-1 flex items-center justify-center p-4 min-h-0">
            <Card className="max-w-md w-full bg-white/5 backdrop-blur-sm border border-white/10">
              <CardBody className="text-center p-6">
                <div className="mb-6">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                    <MessageCircle className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Welcome to AI Career Assistant
                  </h3>
                  <p className="text-gray-300 text-sm">
                    Choose a conversation type and start chatting to get personalized career guidance.
                  </p>
                </div>

                <div className="space-y-4">
                  <Select
                    label="Conversation Type"
                    value={conversationType}
                    onChange={(e) => setConversationType(e.target.value as any)}
                    className="w-full"
                    classNames={{
                      base: "text-white",
                      trigger: "bg-white/10 border-white/20 text-white hover:bg-white/20",
                      value: "text-white",
                      listbox: "bg-slate-800 text-white",
                      popoverContent: "bg-slate-800 border border-white/10",
                      listboxWrapper: "bg-slate-800",
                    }}
                  >
                    <SelectItem key="general" className="text-white hover:bg-white/20">General Chat</SelectItem>
                    <SelectItem key="job_search" className="text-white hover:bg-white/20">Job Search</SelectItem>
                    <SelectItem key="resume_review" className="text-white hover:bg-white/20">Resume Review</SelectItem>
                    <SelectItem key="interview_prep" className="text-white hover:bg-white/20">Interview Prep</SelectItem>
                    <SelectItem key="career_guidance" className="text-white hover:bg-white/20">Career Guidance</SelectItem>
                  </Select>

                  <Button
                    color="primary"
                    size="lg"
                    className="w-full bg-gradient-to-r from-blue-500 to-purple-500 font-semibold"
                    onPress={startNewConversation}
                    isLoading={isLoading}
                    startContent={!isLoading ? <MessageCircle className="w-4 h-4" /> : undefined}
                  >
                    {isLoading ? 'Starting...' : 'Start Conversation'}
                  </Button>

                  {/* Quick Action Buttons */}
                  <div className="pt-4 border-t border-white/10">
                    <p className="text-sm text-gray-400 mb-3 text-center">Or try these quick actions:</p>
                    <div className="grid grid-cols-2 gap-3">
                      <Button
                        variant="bordered"
                        className="border-blue-500/30 hover:border-blue-500/60 text-blue-400 hover:text-blue-300"
                        startContent={<Search className="w-4 h-4" />}
                        onPress={() => {
                          setConversationType('job_search');
                          startNewConversation();
                        }}
                      >
                        Find Jobs
                      </Button>
                      <Button
                        variant="bordered"
                        className="border-purple-500/30 hover:border-purple-500/60 text-purple-400 hover:text-purple-300"
                        startContent={<FileText className="w-4 h-4" />}
                        onPress={() => {
                          setConversationType('resume_review');
                          startNewConversation();
                        }}
                      >
                        Review Resume
                      </Button>
                    </div>
                  </div>
                </div>

                {error && (
                  <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <p className="text-red-400 text-sm">{error}</p>
                  </div>
                )}

              </CardBody>
            </Card>
          </div>
        ) : (
          // Chat Messages
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.message_type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] sm:max-w-[75%] ${
                      message.message_type === 'user'
                        ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                        : 'bg-white/10 text-white border border-white/20'
                    } rounded-2xl px-4 py-3 shadow-lg backdrop-blur-sm`}
                  >
                    <div className="flex items-start gap-2">
                      <Avatar
                        icon={message.message_type === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        size="sm"
                        className={`${
                          message.message_type === 'user' 
                            ? 'bg-white/20' 
                            : 'bg-gradient-to-r from-blue-500 to-purple-500'
                        } flex-shrink-0`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm whitespace-pre-wrap break-words">
                          {message.message_type === 'assistant' && isDisplayingTyping && messages[messages.length - 1].id === message.id 
                            ? renderMessageContent(typingText) + (typingText.length < message.content.length ? '|' : '')
                            : renderMessageContent(message.content)
                          }
                        </div>
                        <div className="flex items-center gap-1 mt-1">
                          <span className="text-xs opacity-70">
                            {formatTimestamp(message.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Typing Indicator */}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-white/10 border border-white/20 rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Avatar
                        icon={<Bot className="w-4 h-4" />}
                        size="sm"
                        className="bg-gradient-to-r from-blue-500 to-purple-500"
                      />
                      <div className="flex items-center gap-1">
                        <span className="text-sm text-gray-300">AI is typing</span>
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
            {/* Resume Upload for Resume Review (active chat area) */}
            {conversationType === 'resume_review' && conversation && (
              <div className="p-4 border-t border-white/10 bg-black/30">
                <h4 className="text-white font-medium mb-2">Upload Your Resume for Review</h4>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={e => setSelectedResume(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-500 file:text-white hover:file:bg-blue-600"
                  disabled={isUploading}
                />
                {selectedResume && (
                  <Button
                    color="primary"
                    className="mt-3 w-full"
                    isLoading={isUploading}
                    onPress={handleResumeUpload}
                  >
                    Upload & Analyze
                  </Button>
                )}
                {lastUploadedFile && improvedResumeContent && (
                  <div className="mt-3 flex gap-2">
                    <Button
                      color="primary"
                      variant="bordered"
                      className="flex-1"
                      onPress={() => setIsPreviewOpen(true)}
                    >
                      👀 View Improved Resume
                    </Button>
                    <Button
                      color="secondary"
                      className="flex-1"
                      isLoading={isUploading}
                      onPress={handleDownloadImprovedResume}
                    >
                      📥 Download
                    </Button>
                  </div>
                )}
                {error && (
                  <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <p className="text-red-400 text-xs">{error}</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Message Input */}
        {conversation && (
          <div className="p-4 bg-black/30 backdrop-blur-sm border-t border-white/10">
            <div className="flex gap-3">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1"
                size="lg"
                classNames={{
                  base: "text-white",
                  input: "text-white placeholder:text-gray-400",
                  inputWrapper: "bg-white/10 border-white/20 hover:bg-white/20 focus:bg-white/20",
                }}
                disabled={isLoading}
              />
              <Button
                color="primary"
                isIconOnly
                size="lg"
                onPress={sendMessage}
                isLoading={isLoading}
                disabled={!inputMessage.trim() || isLoading}
                className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 min-w-[48px]"
              >
                {!isLoading && <Send className="w-5 h-5" />}
              </Button>
            </div>

            {error && (
              <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                <p className="text-red-400 text-xs">{error}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Settings Modal */}
      <Modal 
        isOpen={isOpen} 
        onClose={onClose}
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
            <h3 className="text-lg font-semibold">Chat Settings</h3>
          </ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              {stats && (
                <div className="space-y-2">
                  <h4 className="font-semibold">Statistics</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-white/5 p-3 rounded-lg">
                      <p className="text-gray-400">Total Conversations</p>
                      <p className="font-semibold">{stats.total_conversations}</p>
                    </div>
                    <div className="bg-white/5 p-3 rounded-lg">
                      <p className="text-gray-400">Active Conversations</p>
                      <p className="font-semibold">{stats.active_conversations}</p>
                    </div>
                    <div className="bg-white/5 p-3 rounded-lg">
                      <p className="text-gray-400">Total Messages</p>
                      <p className="font-semibold">{stats.total_messages}</p>
                    </div>
                    <div className="bg-white/5 p-3 rounded-lg">
                      <p className="text-gray-400">Rate Limit</p>
                      <p className="font-semibold">{stats.rate_limit_remaining}/100</p>
                    </div>
                  </div>
                </div>
              )}
              
              {conversation && (
                <div className="space-y-2">
                  <h4 className="font-semibold">Current Conversation</h4>
                  <div className="bg-white/5 p-3 rounded-lg text-sm">
                    <p><strong>Status:</strong> {conversation.status}</p>
                    <p><strong>Type:</strong> {getConversationTypeLabel(conversationType)}</p>
                    <p><strong>Messages:</strong> {messages.length}</p>
                    <p><strong>Started:</strong> {formatTimestamp(conversation.created_at)}</p>
                  </div>
                </div>
              )}
            </div>
          </ModalBody>
          <ModalFooter>
            <Button
              color="danger"
              variant="light"
              onPress={endConversation}
              startContent={<XCircle className="w-4 h-4" />}
              disabled={!conversation}
            >
              End Conversation
            </Button>
            <Button
              color="primary"
              onPress={onClose}
              startContent={<CheckCircle className="w-4 h-4" />}
            >
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Resume Preview Modal */}
      <Modal 
        isOpen={isPreviewOpen} 
        onClose={() => setIsPreviewOpen(false)}
        size="5xl"
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
            <h3 className="text-lg font-semibold">✨ Your Improved Resume Preview</h3>
          </ModalHeader>
          <ModalBody>
            <div className="bg-white/5 rounded-lg p-6 max-h-[60vh] overflow-y-auto">
              <div className="whitespace-pre-wrap font-sans text-sm text-gray-100 leading-relaxed">
                {improvedResumeContent}
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button
              color="danger"
              variant="light"
              onPress={() => setIsPreviewOpen(false)}
            >
              Close
            </Button>
            <Button
              color="primary"
              isLoading={isUploading}
              onPress={() => {
                setIsPreviewOpen(false);
                handleDownloadImprovedResume();
              }}
              startContent={!isUploading && <span>📥</span>}
            >
              Download This Resume
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
      
      {/* Confetti Effect */}
      <ConfettiEffect />
    </div>
  );
} 