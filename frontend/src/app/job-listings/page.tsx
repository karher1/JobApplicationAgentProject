"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Card, 
  CardBody, 
  Button, 
  Chip, 
  Input, 
  Select, 
  SelectItem,
  Pagination,
  Spinner,
  Badge,
  Avatar,
  Link
} from "@heroui/react";
import { SearchIcon, MapPinIcon, BuildingIcon, ClockIcon, EyeIcon, ExternalLinkIcon } from 'lucide-react';
import { jobSearchAPI, JobPosition } from '@/lib/api';

export default function JobListingsPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobPosition[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [jobBoardFilter, setJobBoardFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [expandedDescriptions, setExpandedDescriptions] = useState<Set<string>>(new Set());

  const itemsPerPage = 10;

  useEffect(() => {
    fetchJobs();
  }, [currentPage]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const offset = (currentPage - 1) * itemsPerPage;
      const allJobs = await jobSearchAPI.getJobs(itemsPerPage, offset, jobBoardFilter, locationFilter);
      setJobs(allJobs);
      
      // Calculate total pages (this is a rough estimate since we don't have total count)
      setTotalPages(Math.max(1, Math.ceil(allJobs.length / itemsPerPage) + 1));
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (): "default" | "primary" | "secondary" | "success" | "warning" | "danger" => {
    // Since we don't have status in JobPosition, we'll use a default
    return 'default';
  };

  const getStatusText = () => {
    // Since we don't have status in JobPosition, we'll use a default
    return 'Available';
  };

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         job.company.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLocation = !locationFilter || job.location.toLowerCase().includes(locationFilter.toLowerCase());
    const matchesType = !typeFilter || (job.job_type && job.job_type.toLowerCase() === typeFilter.toLowerCase());
    const matchesJobBoard = !jobBoardFilter || job.job_board.toLowerCase().includes(jobBoardFilter.toLowerCase());
    
    return matchesSearch && matchesLocation && matchesType && matchesJobBoard;
  });

  const handleViewDetails = (jobId: string) => {
    router.push(`/job/${jobId}`);
  };

  const toggleDescription = (jobId: string) => {
    const newExpanded = new Set(expandedDescriptions);
    if (expandedDescriptions.has(jobId)) {
      newExpanded.delete(jobId);
    } else {
      newExpanded.add(jobId);
    }
    setExpandedDescriptions(newExpanded);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const truncateDescription = (description: string, isExpanded: boolean) => {
    if (!description) return 'No description available.';
    if (isExpanded) return description;
    return description.length > 200 ? description.substring(0, 200) + '...' : description;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" color="primary" />
          <p className="mt-4 text-gray-600">Loading job listings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Job Listings</h1>
          <p className="text-gray-600">Find your next career opportunity</p>
        </div>

        {/* Search and Filters */}
        <Card className="mb-6">
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <Input
                placeholder="Search jobs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                startContent={<SearchIcon className="w-4 h-4 text-gray-400" />}
                className="md:col-span-2"
              />
              <Input
                placeholder="Location..."
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                startContent={<MapPinIcon className="w-4 h-4 text-gray-400" />}
              />
              <Select
                placeholder="Job Type"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                startContent={<ClockIcon className="w-4 h-4 text-gray-400" />}
              >
                <SelectItem key="">All Types</SelectItem>
                <SelectItem key="full-time">Full-time</SelectItem>
                <SelectItem key="part-time">Part-time</SelectItem>
                <SelectItem key="contract">Contract</SelectItem>
                <SelectItem key="internship">Internship</SelectItem>
              </Select>
              <Select
                placeholder="Job Board"
                value={jobBoardFilter}
                onChange={(e) => setJobBoardFilter(e.target.value)}
              >
                <SelectItem key="">All Boards</SelectItem>
                <SelectItem key="stripe">Stripe</SelectItem>
                <SelectItem key="greenhouse">Greenhouse</SelectItem>
                <SelectItem key="lever">Lever</SelectItem>
                <SelectItem key="ashby">Ashby</SelectItem>
              </Select>
            </div>
            <div className="mt-4">
              <Button
                color="primary"
                variant="flat"
                onPress={fetchJobs}
                startContent={<SearchIcon className="w-4 h-4" />}
              >
                Refresh Jobs
              </Button>
            </div>
          </CardBody>
        </Card>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-gray-600">
            Showing {filteredJobs.length} of {jobs.length} jobs
          </p>
        </div>

        {/* Job Cards */}
        <div className="space-y-4 mb-8">
          {filteredJobs.map((job) => {
            const jobId = job.id || `${job.company}-${job.title}-${job.posted_date}`;
            const isExpanded = expandedDescriptions.has(jobId);
            
            return (
              <Card key={jobId} className="hover:shadow-lg transition-shadow duration-300">
                <CardBody>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Avatar
                          name={job.company}
                          className="w-10 h-10"
                          color="primary"
                        />
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {job.title}
                          </h3>
                          <p className="text-gray-600 flex items-center gap-1">
                            <BuildingIcon className="w-4 h-4" />
                            {job.company}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 mb-3 flex-wrap">
                        {/* Show location if it's not just "Remote" or if no remote_option exists */}
                        {job.location && job.location.toLowerCase() !== 'remote' && (
                          <div className="flex items-center gap-1 text-gray-500">
                            <MapPinIcon className="w-4 h-4" />
                            <span className="text-sm">{job.location}</span>
                          </div>
                        )}
                        <Chip size="sm" variant="flat" color="primary">
                          {job.job_board}
                        </Chip>
                        {job.job_type && (
                          <Chip size="sm" variant="flat" color="secondary">
                            {job.job_type}
                          </Chip>
                        )}
                        {/* Show remote option, or location if it's remote and no remote_option */}
                        {job.remote_option ? (
                          <Chip size="sm" variant="flat" color="success">
                            {job.remote_option}
                          </Chip>
                        ) : job.location && job.location.toLowerCase() === 'remote' && (
                          <Chip size="sm" variant="flat" color="success">
                            Remote
                          </Chip>
                        )}
                        {job.salary_range && (
                          <Chip size="sm" variant="flat" color="warning">
                            {job.salary_range}
                          </Chip>
                        )}
                      </div>
                      
                      {/* Enhanced Job Description */}
                      <div className="mb-3">
                        <p className="text-gray-600 text-sm leading-relaxed">
                          {truncateDescription(job.description_snippet || '', isExpanded)}
                        </p>
                        {job.description_snippet && job.description_snippet.length > 200 && (
                          <Button
                            size="sm"
                            variant="light"
                            color="primary"
                            onPress={() => toggleDescription(jobId)}
                            className="mt-1 h-6 min-h-6 px-2"
                          >
                            {isExpanded ? 'Show Less' : 'Show More'}
                          </Button>
                        )}
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge color={getStatusColor()} variant="flat">
                            {getStatusText()}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            Posted {formatDate(job.posted_date)}
                          </span>
                        </div>
                        
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="flat" 
                            color="primary"
                            onPress={() => handleViewDetails(jobId)}
                            startContent={<EyeIcon className="w-4 h-4" />}
                          >
                            View Details
                          </Button>
                          <Button 
                            size="sm" 
                            variant="flat"
                            as={Link}
                            href={job.url}
                            target="_blank"
                            startContent={<ExternalLinkIcon className="w-4 h-4" />}
                          >
                            Apply
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            );
          })}
        </div>

        {/* Empty State */}
        {filteredJobs.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <SearchIcon className="w-16 h-16 mx-auto mb-4" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No jobs found</h3>
            <p className="text-gray-600 mb-4">
              Try adjusting your search filters or refresh the job listings.
            </p>
            <Button
              color="primary"
              onPress={fetchJobs}
            >
              Refresh Jobs
            </Button>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && filteredJobs.length > 0 && (
          <div className="flex justify-center">
            <Pagination
              total={totalPages}
              page={currentPage}
              onChange={setCurrentPage}
              showControls
              color="primary"
            />
          </div>
        )}
      </div>
    </div>
  );
} 