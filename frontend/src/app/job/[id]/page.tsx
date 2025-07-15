"use client";

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  Card, 
  CardBody, 
  CardHeader, 
  Button, 
  Chip, 
  Spinner,
  Badge,
  Divider,
  Avatar,
  Link
} from "@heroui/react";
import { ArrowLeftIcon, MapPinIcon, BuildingIcon, ClockIcon, CalendarIcon, ExternalLinkIcon, BookmarkIcon, ShareIcon } from 'lucide-react';
import { jobSearchAPI, JobPosition } from '@/lib/api';

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [job, setJob] = useState<JobPosition | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const jobId = params.id as string;

  useEffect(() => {
    const fetchJob = async () => {
      if (!jobId) return;
      
      try {
        setLoading(true);
        const jobData = await jobSearchAPI.getJob(jobId);
        setJob(jobData);
      } catch (err) {
        console.error('Error fetching job:', err);
        setError('Failed to load job details');
      } finally {
        setLoading(false);
      }
    };

    fetchJob();
  }, [jobId]);

  const handleBack = () => {
    router.back();
  };

  const handleSave = () => {
    setSaved(!saved);
    // TODO: Implement actual save functionality with API
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: job?.title,
        text: `Check out this job: ${job?.title} at ${job?.company}`,
        url: window.location.href,
      });
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" color="primary" />
          <p className="mt-4 text-gray-600">Loading job details...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Job Not Found</h2>
          <p className="text-gray-600 mb-4">{error || 'The job you\'re looking for doesn\'t exist.'}</p>
          <Button color="primary" onPress={handleBack}>
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header with back button */}
          <div className="mb-6">
            <Button
              variant="flat"
              color="primary"
              startContent={<ArrowLeftIcon className="w-4 h-4" />}
              onPress={handleBack}
              className="mb-4"
            >
              Back to Jobs
            </Button>
          </div>

          {/* Main job card */}
          <Card className="mb-6">
            <CardHeader className="pb-4">
              <div className="w-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <Avatar
                      name={job.company}
                      className="w-16 h-16"
                      color="primary"
                    />
                    <div>
                      <h1 className="text-2xl font-bold text-gray-900 mb-1">
                        {job.title}
                      </h1>
                      <p className="text-lg text-gray-600 flex items-center gap-2">
                        <BuildingIcon className="w-5 h-5" />
                        {job.company}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      isIconOnly
                      variant="flat"
                      color={saved ? "warning" : "default"}
                      onPress={handleSave}
                    >
                      <BookmarkIcon className={`w-4 h-4 ${saved ? 'fill-current' : ''}`} />
                    </Button>
                    <Button
                      isIconOnly
                      variant="flat"
                      onPress={handleShare}
                    >
                      <ShareIcon className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Job meta information */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-2 text-gray-600">
                    <MapPinIcon className="w-4 h-4" />
                    <span>{job.location}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <ClockIcon className="w-4 h-4" />
                    <span>{job.job_type || 'Full-time'}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <CalendarIcon className="w-4 h-4" />
                    <span>Posted {formatDate(job.posted_date)}</span>
                  </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-2 mt-4">
                  <Chip size="sm" variant="flat" color="primary">
                    {job.job_board}
                  </Chip>
                  {job.remote_option && (
                    <Chip size="sm" variant="flat" color="success">
                      {job.remote_option}
                    </Chip>
                  )}
                  {job.salary_range && (
                    <Chip size="sm" variant="flat" color="warning">
                      {job.salary_range}
                    </Chip>
                  )}
                </div>
              </div>
            </CardHeader>

            <Divider />

            <CardBody>
              {/* Job Description */}
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-3">Job Description</h2>
                <div className="prose max-w-none text-gray-700">
                  {job.description_snippet ? (
                    <p className="whitespace-pre-wrap leading-relaxed">
                      {job.description_snippet}
                    </p>
                  ) : (
                    <p className="text-gray-500 italic">
                      No detailed description available. Click "Apply Now" to view full details on the company's website.
                    </p>
                  )}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  as={Link}
                  href={job.url}
                  target="_blank"
                  color="primary"
                  size="lg"
                  className="flex-1"
                  endContent={<ExternalLinkIcon className="w-4 h-4" />}
                >
                  Apply Now
                </Button>
                <Button
                  variant="flat"
                  color="secondary"
                  size="lg"
                  className="flex-1"
                  onPress={() => {
                    // TODO: Implement similar jobs functionality
                    console.log('Find similar jobs for:', job.title);
                  }}
                >
                  Find Similar Jobs
                </Button>
              </div>
            </CardBody>
          </Card>

          {/* Additional information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Job Details */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Job Details</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Company:</span>
                    <span className="font-medium">{job.company}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Location:</span>
                    <span className="font-medium">{job.location}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Job Board:</span>
                    <span className="font-medium">{job.job_board}</span>
                  </div>
                  {job.job_type && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="font-medium">{job.job_type}</span>
                    </div>
                  )}
                  {job.salary_range && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Salary:</span>
                      <span className="font-medium text-green-600">{job.salary_range}</span>
                    </div>
                  )}
                  {job.remote_option && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Remote:</span>
                      <span className="font-medium">{job.remote_option}</span>
                    </div>
                  )}
                </div>
              </CardBody>
            </Card>

            {/* Application Status */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Application Status</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Badge color="default" variant="flat">Not Applied</Badge>
                  </div>
                  <p className="text-sm text-gray-600">
                    Ready to apply? Click "Apply Now" to be redirected to the company's application page.
                  </p>
                  <div className="space-y-2 text-sm">
                    <p><strong>Tip:</strong> Tailor your resume to match the job requirements.</p>
                    <p><strong>Note:</strong> Applications are tracked automatically when you apply through our system.</p>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
} 