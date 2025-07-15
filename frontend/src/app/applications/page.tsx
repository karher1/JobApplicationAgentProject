'use client';

import { useState, useEffect } from 'react';
import { Card, CardBody, CardHeader, Button, Chip, Spinner, Pagination, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Textarea } from '@heroui/react';
import { pendingApplicationAPI, PendingApplication, PendingApplicationListResponse } from '@/lib/api';

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<PendingApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalApplications, setTotalApplications] = useState(0);
  const [selectedApplication, setSelectedApplication] = useState<PendingApplication | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve');
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Mock user ID - in real app, get from auth context
  const userId = 1;

  useEffect(() => {
    loadApplications();
  }, [currentPage, statusFilter]);

  const loadApplications = async () => {
    try {
      const response = await pendingApplicationAPI.getUserPendingApplications(
        userId,
        statusFilter || undefined,
        10,
        (currentPage - 1) * 10
      );
      setApplications(response.applications);
      setTotalApplications(response.total);
    } catch (error) {
      console.error('Error loading applications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = (application: PendingApplication) => {
    setSelectedApplication(application);
    setReviewModalOpen(true);
  };

  const submitReview = async () => {
    if (!selectedApplication) return;

    try {
      await pendingApplicationAPI.reviewPendingApplication(
        selectedApplication.id,
        userId,
        {
          action: reviewAction,
          notes: reviewNotes,
        }
      );
      setReviewModalOpen(false);
      setReviewNotes('');
      setSelectedApplication(null);
      await loadApplications();
    } catch (error) {
      console.error('Error submitting review:', error);
    }
  };

  const handleCancelApplication = async (applicationId: number) => {
    try {
      await pendingApplicationAPI.cancelPendingApplication(applicationId, userId);
      await loadApplications();
    } catch (error) {
      console.error('Error canceling application:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending': return 'warning';
      case 'approved': return 'success';
      case 'rejected': return 'danger';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return 'danger';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
            Applications
          </h1>
          <p className="text-gray-300 text-lg">
            Track and manage your job applications
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-6 bg-white/5 backdrop-blur-sm border border-white/10">
          <CardBody className="p-4">
            <div className="flex gap-4 items-center">
                             <select
                 value={statusFilter}
                 onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
                 className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
               >
                <option value="">All Status</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </CardBody>
        </Card>

        {/* Applications List */}
        <div className="space-y-4">
          {applications.length > 0 ? (
            <>
              <div className="flex justify-between items-center mb-4">
                <p className="text-gray-300">
                  {totalApplications} application(s) found
                </p>
                <Pagination
                  total={Math.ceil(totalApplications / 10)}
                  page={currentPage}
                  onChange={setCurrentPage}
                  color="primary"
                />
              </div>

              <div className="grid gap-4">
                {applications.map((application) => (
                  <Card key={application.id} className="bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all">
                    <CardBody className="p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-semibold text-white mb-2">
                            {application.job_title}
                          </h3>
                          <p className="text-gray-300 mb-2">{application.company_name}</p>
                          <div className="flex items-center gap-4 text-gray-400 text-sm">
                            <span>Applied: {formatDate(application.created_at)}</span>
                            <span>Updated: {formatDate(application.updated_at)}</span>
                          </div>
                        </div>
                        <div className="flex flex-col gap-2">
                          <Chip color={getStatusColor(application.status) as any} size="sm">
                            {application.status}
                          </Chip>
                          <Chip color={getPriorityColor(application.priority) as any} size="sm">
                            {application.priority}
                          </Chip>
                        </div>
                      </div>

                      {application.notes && (
                        <div className="mb-4">
                          <p className="text-gray-300 text-sm">
                            <strong>Notes:</strong> {application.notes}
                          </p>
                        </div>
                      )}

                      <div className="flex justify-between items-center">
                        <div className="flex gap-2">
                          {application.status === 'pending' && (
                            <>
                              <Button
                                color="success"
                                size="sm"
                                onClick={() => {
                                  setReviewAction('approve');
                                  handleReview(application);
                                }}
                              >
                                Approve
                              </Button>
                              <Button
                                color="danger"
                                size="sm"
                                onClick={() => {
                                  setReviewAction('reject');
                                  handleReview(application);
                                }}
                              >
                                Reject
                              </Button>
                            </>
                          )}
                          {application.status === 'pending' && (
                            <Button
                              color="default"
                              size="sm"
                              onClick={() => handleCancelApplication(application.id)}
                            >
                              Cancel
                            </Button>
                          )}
                        </div>
                        <Button
                          color="primary"
                          size="sm"
                          variant="bordered"
                          onClick={() => {
                            setSelectedApplication(application);
                            setReviewModalOpen(true);
                          }}
                        >
                          View Details
                        </Button>
                      </div>
                    </CardBody>
                  </Card>
                ))}
              </div>
            </>
          ) : (
            <Card className="bg-white/5 backdrop-blur-sm border border-white/10">
              <CardBody className="text-center py-12">
                <p className="text-gray-400 text-lg">
                  No applications found. Start by searching for jobs and applying!
                </p>
              </CardBody>
            </Card>
          )}
        </div>

        {/* Review Modal */}
        <Modal isOpen={reviewModalOpen} onClose={() => setReviewModalOpen(false)} size="2xl">
          <ModalContent className="bg-slate-800 border border-white/10">
            <ModalHeader className="text-white">
              Review Application
            </ModalHeader>
            <ModalBody>
              {selectedApplication && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-white font-semibold mb-2">Application Details</h3>
                    <div className="bg-white/5 p-4 rounded-lg space-y-2">
                      <p className="text-gray-300"><strong>Job:</strong> {selectedApplication.job_title}</p>
                      <p className="text-gray-300"><strong>Company:</strong> {selectedApplication.company_name}</p>
                      <p className="text-gray-300"><strong>Status:</strong> {selectedApplication.status}</p>
                      <p className="text-gray-300"><strong>Priority:</strong> {selectedApplication.priority}</p>
                      <p className="text-gray-300"><strong>Applied:</strong> {formatDate(selectedApplication.created_at)}</p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-white font-semibold mb-2">Review Decision</h3>
                    <div className="flex gap-4">
                      <Button
                        color={reviewAction === 'approve' ? 'success' : 'default'}
                        variant={reviewAction === 'approve' ? 'solid' : 'bordered'}
                        onClick={() => setReviewAction('approve')}
                      >
                        Approve
                      </Button>
                      <Button
                        color={reviewAction === 'reject' ? 'danger' : 'default'}
                        variant={reviewAction === 'reject' ? 'solid' : 'bordered'}
                        onClick={() => setReviewAction('reject')}
                      >
                        Reject
                      </Button>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-white font-semibold mb-2">Review Notes</h3>
                                         <Textarea
                       placeholder="Add notes about your decision..."
                       value={reviewNotes}
                       onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setReviewNotes(e.target.value)}
                       className="bg-white/5"
                     />
                  </div>

                  {selectedApplication.cover_letter && (
                    <div>
                      <h3 className="text-white font-semibold mb-2">Cover Letter</h3>
                      <div className="bg-white/5 p-4 rounded-lg">
                        <p className="text-gray-300 text-sm whitespace-pre-wrap">
                          {selectedApplication.cover_letter}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </ModalBody>
            <ModalFooter>
              <Button color="default" variant="bordered" onPress={() => setReviewModalOpen(false)}>
                Cancel
              </Button>
              <Button 
                color={reviewAction === 'approve' ? 'success' : 'danger'} 
                onPress={submitReview}
              >
                {reviewAction === 'approve' ? 'Approve' : 'Reject'} Application
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>
    </div>
  );
} 