"""
Data models for AI content generation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    COVER_LETTER = "cover_letter"
    ESSAY_ANSWER = "essay_answer"
    SHORT_RESPONSE = "short_response"


class QuestionType(str, Enum):
    MOTIVATION = "motivation"
    EXPERIENCE = "experience"
    STRENGTHS = "strengths"
    CHALLENGES = "challenges"
    GOALS = "goals"
    TEAMWORK = "teamwork"
    ABOUT_YOU = "about_you"
    GENERAL = "general"


class JobData(BaseModel):
    """Job information for content generation"""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: Optional[str] = Field(None, description="Job description")
    url: Optional[str] = Field(None, description="Job posting URL")
    location: Optional[str] = Field(None, description="Job location")
    requirements: Optional[List[str]] = Field(None, description="Job requirements")
    benefits: Optional[List[str]] = Field(None, description="Job benefits")
    salary_range: Optional[str] = Field(None, description="Salary information")


class FieldContext(BaseModel):
    """Context about a specific form field"""
    label: str = Field(..., description="Field label or question")
    field_type: str = Field(..., description="Type of field (textarea, input, etc.)")
    placeholder: Optional[str] = Field(None, description="Field placeholder text")
    max_length: Optional[int] = Field(None, description="Maximum character length")
    required: bool = Field(default=False, description="Whether field is required")


# Request Models
class CoverLetterRequest(BaseModel):
    """Request to generate a cover letter"""
    user_id: int = Field(..., description="User ID")
    job_data: JobData = Field(..., description="Job information")
    tone: Optional[str] = Field("professional", description="Tone of the letter")
    max_words: Optional[int] = Field(400, description="Maximum word count")


class EssayQuestionRequest(BaseModel):
    """Request to answer an essay question"""
    user_id: int = Field(..., description="User ID")
    job_data: JobData = Field(..., description="Job information")
    question: str = Field(..., description="The essay question to answer")
    field_context: Optional[FieldContext] = Field(None, description="Field context")
    max_words: Optional[int] = Field(300, description="Maximum word count")


class ShortResponseRequest(BaseModel):
    """Request to generate a short response"""
    user_id: int = Field(..., description="User ID")
    job_data: JobData = Field(..., description="Job information")
    field_label: str = Field(..., description="Field label or prompt")
    field_context: Optional[FieldContext] = Field(None, description="Field context")
    max_words: Optional[int] = Field(50, description="Maximum word count")


class BatchContentRequest(BaseModel):
    """Request to generate multiple pieces of content"""
    user_id: int = Field(..., description="User ID")
    job_data: JobData = Field(..., description="Job information")
    fields: List[FieldContext] = Field(..., description="List of fields to generate content for")


# Response Models
class ContentGenerationResult(BaseModel):
    """Result of content generation"""
    success: bool = Field(..., description="Whether generation was successful")
    content: Optional[str] = Field(None, description="Generated content")
    word_count: Optional[int] = Field(None, description="Word count of generated content")
    content_type: ContentType = Field(..., description="Type of content generated")
    question: Optional[str] = Field(None, description="Original question (for essays)")
    question_type: Optional[QuestionType] = Field(None, description="Classified question type")
    field_label: Optional[str] = Field(None, description="Field label (for short responses)")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    generated_at: datetime = Field(default_factory=datetime.now, description="Generation timestamp")
    job_title: Optional[str] = Field(None, description="Job title for reference")
    company: Optional[str] = Field(None, description="Company name for reference")


class BatchContentResponse(BaseModel):
    """Response for batch content generation"""
    user_id: int = Field(..., description="User ID")
    job_data: JobData = Field(..., description="Job information")
    results: List[ContentGenerationResult] = Field(..., description="Generation results")
    total_fields: int = Field(..., description="Total number of fields processed")
    successful_generations: int = Field(..., description="Number of successful generations")
    failed_generations: int = Field(..., description="Number of failed generations")
    total_words: int = Field(..., description="Total words generated")
    generated_at: datetime = Field(default_factory=datetime.now, description="Batch generation timestamp")


# Analysis Models
class ContentAnalysis(BaseModel):
    """Analysis of generated content"""
    content: str = Field(..., description="Content to analyze")
    word_count: int = Field(..., description="Word count")
    sentence_count: int = Field(..., description="Sentence count")
    reading_level: Optional[str] = Field(None, description="Estimated reading level")
    tone_analysis: Optional[Dict[str, float]] = Field(None, description="Tone analysis scores")
    keyword_density: Optional[Dict[str, float]] = Field(None, description="Keyword density analysis")
    sentiment_score: Optional[float] = Field(None, description="Sentiment analysis score")


class ContentSuggestion(BaseModel):
    """Suggestion for content improvement"""
    type: str = Field(..., description="Type of suggestion")
    message: str = Field(..., description="Suggestion message")
    severity: str = Field(..., description="Severity level (low, medium, high)")
    suggested_change: Optional[str] = Field(None, description="Suggested change")


class ContentFeedback(BaseModel):
    """Feedback and suggestions for generated content"""
    content_id: str = Field(..., description="Unique identifier for the content")
    analysis: ContentAnalysis = Field(..., description="Content analysis")
    suggestions: List[ContentSuggestion] = Field(..., description="Improvement suggestions")
    overall_score: float = Field(..., description="Overall quality score (0-1)")
    meets_requirements: bool = Field(..., description="Whether content meets basic requirements")


# History Models
class ContentHistory(BaseModel):
    """Historical record of generated content"""
    id: str = Field(..., description="Unique identifier")
    user_id: int = Field(..., description="User ID")
    content_type: ContentType = Field(..., description="Type of content")
    job_title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    question: Optional[str] = Field(None, description="Original question")
    generated_content: str = Field(..., description="Generated content")
    word_count: int = Field(..., description="Word count")
    user_rating: Optional[int] = Field(None, description="User rating (1-5)")
    was_used: bool = Field(default=False, description="Whether content was actually used")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class ContentTemplate(BaseModel):
    """Template for content generation"""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    content_type: ContentType = Field(..., description="Type of content")
    template_text: str = Field(..., description="Template content with placeholders")
    variables: List[str] = Field(..., description="List of template variables")
    industry: Optional[str] = Field(None, description="Target industry")
    job_level: Optional[str] = Field(None, description="Target job level")
    created_by: str = Field(..., description="Creator of the template")
    is_active: bool = Field(default=True, description="Whether template is active")
    usage_count: int = Field(default=0, description="Number of times used")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


# Settings Models
class ContentGenerationSettings(BaseModel):
    """User settings for content generation"""
    user_id: int = Field(..., description="User ID")
    default_tone: str = Field(default="professional", description="Default tone for content")
    max_cover_letter_words: int = Field(default=400, description="Max words for cover letters")
    max_essay_words: int = Field(default=300, description="Max words for essay answers")
    max_short_response_words: int = Field(default=50, description="Max words for short responses")
    include_specific_examples: bool = Field(default=True, description="Include specific examples")
    personalization_level: str = Field(default="high", description="Level of personalization")
    auto_generate_cover_letters: bool = Field(default=True, description="Auto-generate cover letters")
    review_before_use: bool = Field(default=True, description="Review content before using")
    save_generation_history: bool = Field(default=True, description="Save generation history")
    preferred_writing_style: str = Field(default="concise", description="Preferred writing style")
    created_at: datetime = Field(default_factory=datetime.now, description="Settings creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


# Validation Models
class ContentValidation(BaseModel):
    """Validation rules for generated content"""
    min_words: Optional[int] = Field(None, description="Minimum word count")
    max_words: Optional[int] = Field(None, description="Maximum word count")
    required_keywords: Optional[List[str]] = Field(None, description="Required keywords")
    forbidden_words: Optional[List[str]] = Field(None, description="Forbidden words")
    must_include_company: bool = Field(default=True, description="Must mention company name")
    must_include_position: bool = Field(default=True, description="Must mention position")
    max_repetition_percentage: float = Field(default=0.1, description="Max percentage of repeated phrases")
    readability_score_min: Optional[float] = Field(None, description="Minimum readability score")


class ValidationResult(BaseModel):
    """Result of content validation"""
    is_valid: bool = Field(..., description="Whether content passed validation")
    violations: List[str] = Field(..., description="List of validation violations")
    warnings: List[str] = Field(..., description="List of warnings")
    score: float = Field(..., description="Overall validation score (0-1)")
    suggestions: List[str] = Field(..., description="Suggestions for improvement")