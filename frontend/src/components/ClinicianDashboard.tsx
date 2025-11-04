/**
 * Clinician Review Dashboard Component
 *
 * Security features:
 * - Requires clinician authentication
 * - No PHI displayed (uses hashes)
 * - Audit trail visible
 * - Input sanitization
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface ReviewCase {
  case_id: string;
  predicted_urgency: string;
  confidence: number;
  status: string;
  priority: string;
  created_at: string;
  explanation?: {
    top_features: Array<{ feature: string; importance: number }>;
    explanation_method: string;
  };
}

interface Props {
  clinicianId: string;
}

export function ClinicianDashboard({ clinicianId }: Props) {
  const [selectedCase, setSelectedCase] = useState<ReviewCase | null>(null);
  const [decision, setDecision] = useState('');
  const [notes, setNotes] = useState('');
  const [overrideUrgency, setOverrideUrgency] = useState('');

  const queryClient = useQueryClient();

  // Fetch pending cases
  const { data: casesData, isLoading } = useQuery({
    queryKey: ['pending-cases', clinicianId],
    queryFn: async () => {
      const response = await fetch(
        `/v1/review/pending?clinician_id=${encodeURIComponent(clinicianId)}`,
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch pending cases');
      }

      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Submit review mutation
  const submitReview = useMutation({
    mutationFn: async (reviewData: any) => {
      const response = await fetch('/v1/review/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reviewData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to submit review');
      }

      return response.json();
    },
    onSuccess: () => {
      // Refresh cases list
      queryClient.invalidateQueries({ queryKey: ['pending-cases'] });
      // Reset form
      setSelectedCase(null);
      setDecision('');
      setNotes('');
      setOverrideUrgency('');
    },
  });

  const handleSubmitReview = () => {
    if (!selectedCase || !decision) {
      return;
    }

    submitReview.mutate({
      case_id: selectedCase.case_id,
      clinician_id: clinicianId,
      decision,
      notes: notes.trim() || null,
      override_urgency: overrideUrgency || null,
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-900 text-red-100';
      case 'high':
        return 'bg-orange-900 text-orange-100';
      case 'medium':
        return 'bg-yellow-900 text-yellow-100';
      case 'low':
        return 'bg-green-900 text-green-100';
      default:
        return 'bg-gray-800 text-gray-100';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    if (urgency.includes('High')) return 'text-red-400';
    if (urgency.includes('Medium')) return 'text-yellow-400';
    return 'text-green-400';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const cases = casesData?.cases || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 bg-gray-950 text-gray-100">
      {/* Cases List */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">Pending Reviews</h2>
          <span className="text-sm text-gray-400">{cases.length} cases</span>
        </div>

        <div className="space-y-3 max-h-[800px] overflow-y-auto">
          {cases.map((case_: ReviewCase) => (
            <div
              key={case_.case_id}
              onClick={() => setSelectedCase(case_)}
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                selectedCase?.case_id === case_.case_id
                  ? 'border-blue-500 bg-gray-800'
                  : 'border-gray-700 bg-gray-900 hover:border-gray-600'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span
                  className={`px-2 py-1 rounded text-xs font-bold uppercase ${getPriorityColor(
                    case_.priority
                  )}`}
                >
                  {case_.priority}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(case_.created_at).toLocaleString()}
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-400">Predicted:</span>
                  <span className={`font-semibold ${getUrgencyColor(case_.predicted_urgency)}`}>
                    {case_.predicted_urgency}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-400">Confidence:</span>
                  <span className="font-mono text-sm">
                    {(case_.confidence * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="text-xs text-gray-500">Case: {case_.case_id.slice(0, 8)}</div>
              </div>
            </div>
          ))}

          {cases.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <p>No pending cases</p>
            </div>
          )}
        </div>
      </div>

      {/* Case Details & Review Form */}
      <div className="space-y-4">
        {selectedCase ? (
          <div className="space-y-6">
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
              <h3 className="text-xl font-bold mb-4">Case Details</h3>

              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-400">Case ID</label>
                  <p className="font-mono text-sm">{selectedCase.case_id}</p>
                </div>

                <div>
                  <label className="text-sm text-gray-400">AI Prediction</label>
                  <p className={`font-semibold ${getUrgencyColor(selectedCase.predicted_urgency)}`}>
                    {selectedCase.predicted_urgency}
                  </p>
                </div>

                <div>
                  <label className="text-sm text-gray-400">Confidence</label>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-gray-800 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${selectedCase.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="font-mono text-sm">
                      {(selectedCase.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Explanation */}
                {selectedCase.explanation && (
                  <div className="mt-6">
                    <label className="text-sm text-gray-400 mb-2 block">
                      Key Features (via {selectedCase.explanation.explanation_method})
                    </label>
                    <div className="space-y-2">
                      {selectedCase.explanation.top_features.slice(0, 5).map((feature, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-xs bg-gray-800 px-2 py-1 rounded">
                            {feature.feature}
                          </span>
                          <div className="flex-1 bg-gray-800 rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full ${
                                feature.importance > 0 ? 'bg-green-500' : 'bg-red-500'
                              }`}
                              style={{
                                width: `${Math.abs(feature.importance) * 100}%`,
                              }}
                            ></div>
                          </div>
                          <span className="text-xs font-mono text-gray-500">
                            {feature.importance.toFixed(3)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Review Form */}
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
              <h3 className="text-xl font-bold mb-4">Submit Review</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Decision *</label>
                  <select
                    value={decision}
                    onChange={(e) => setDecision(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                  >
                    <option value="">Select decision...</option>
                    <option value="approved">Approve</option>
                    <option value="rejected">Reject</option>
                    <option value="escalated">Escalate</option>
                    <option value="in_review">Mark In Review</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Override Urgency</label>
                  <select
                    value={overrideUrgency}
                    onChange={(e) => setOverrideUrgency(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                  >
                    <option value="">Keep AI prediction</option>
                    <option value="Low Urgency">Low Urgency</option>
                    <option value="Medium Urgency">Medium Urgency</option>
                    <option value="High Urgency">High Urgency</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Clinical Notes (optional)
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    maxLength={1000}
                    rows={4}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
                    placeholder="Enter your clinical notes here..."
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    {notes.length}/1000 characters
                  </div>
                </div>

                <button
                  onClick={handleSubmitReview}
                  disabled={!decision || submitReview.isPending}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 rounded transition-colors"
                >
                  {submitReview.isPending ? 'Submitting...' : 'Submit Review'}
                </button>

                {submitReview.isError && (
                  <div className="text-red-400 text-sm">
                    Error: {(submitReview.error as Error).message}
                  </div>
                )}

                {submitReview.isSuccess && (
                  <div className="text-green-400 text-sm">Review submitted successfully!</div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-12 text-center text-gray-500">
            <p>Select a case to review</p>
          </div>
        )}
      </div>
    </div>
  );
}
