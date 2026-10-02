// D:\carbon_ledger\admin\src\services\reviewService.js
//
// CT-FINAL-03 (package 09 §4.6) — `review_audit_trail` is fail-closed (RLS
// enabled, ZERO policies). The four client-side audit INSERTs are removed:
// an authenticated browser must not be able to manufacture audit records
// (`review_audit_trail` is the integrity record for review assignment), and no
// server-side authorisation existed for them. Audit reads now go through the
// existing admin-gated route `/api/admin/reviews/history/audit`.
import { supabase } from '../supabaseClient';
import { adminFetch } from './adminApi';

// Fetch all staff members (users with staff role)
export const fetchStaffMembers = async () => {
  const { data, error } = await supabase
    .from('staff_profiles')
    .select(`
      *,
      auth_users:user_id (
        id,
        email,
        created_at
      )
    `)
    .eq('is_active', true)
    .order('first_name', { ascending: true });

  if (error) throw error;
  return data || [];
};

// Assign review to staff member
export const assignReviewToStaff = async (reviewId, staffUserId, assignedBy) => {
  const { data, error } = await supabase
    .from('manual_review_queue')
    .update({
      assigned_to: staffUserId,
      assigned_by: assignedBy,
      status: 'assigned',
      updated_at: new Date().toISOString()
    })
    .eq('id', reviewId)
    .select()
    .single();

  if (error) throw error;

  // CT-FINAL-03: the audit INSERT that used to run here was removed — the audit
  // trail is now server-authored only (see the file header).

  return data;
};

// Start working on a review
export const startReview = async (reviewId, staffUserId) => {
  const { data, error } = await supabase
    .from('manual_review_queue')
    .update({
      status: 'in_progress',
      started_at: new Date().toISOString()
    })
    .eq('id', reviewId)
    .eq('assigned_to', staffUserId)
    .select()
    .single();

  if (error) throw error;

  // CT-FINAL-03: the 'started' audit INSERT that used to run here was removed.

  return data;
};

// Submit completed review with data entry
export const submitReview = async (reviewId, staffUserId, dataEntry, notes) => {
  const startTime = new Date();
  
  // Get the review to calculate time spent
  const { data: review } = await supabase
    .from('manual_review_queue')
    .select('started_at')
    .eq('id', reviewId)
    .single();

  const timeSpent = review?.started_at 
    ? Math.floor((new Date() - new Date(review.started_at)) / 1000)
    : 0;

  const { data, error } = await supabase
    .from('manual_review_queue')
    .update({
      status: 'completed',
      completed_at: new Date().toISOString(),
      completed_by: staffUserId,
      manual_extraction_result: dataEntry,
      staff_notes: notes,
      data_entry: dataEntry,
      review_time_seconds: timeSpent
    })
    .eq('id', reviewId)
    .eq('assigned_to', staffUserId)
    .select()
    .single();

  if (error) throw error;

  // Update staff stats
  await supabase
    .from('staff_profiles')
    .update({
      total_reviews_completed: supabase.raw('total_reviews_completed + 1'),
      avg_review_time_minutes: supabase.raw('(avg_review_time_minutes * total_reviews_completed + ?) / (total_reviews_completed + 1)', [timeSpent / 60])
    })
    .eq('user_id', staffUserId);

  // CT-FINAL-03: the 'completed' audit INSERT that used to run here was removed.

  return data;
};

// Get review audit trail
export const getReviewAuditTrail = async (reviewId) => {
  // CT-FINAL-03 (package 09 §4.6) — read through the admin-gated backend route.
  const params = new URLSearchParams();
  if (reviewId) params.set('review_id', reviewId);
  const qs = params.toString();

  const result = await adminFetch(
    `/api/admin/reviews/history/audit${qs ? `?${qs}` : ''}`
  );
  return (result && result.data) || [];
};

// Get staff member by user ID
export const getStaffProfile = async (userId) => {
  const { data, error } = await supabase
    .from('staff_profiles')
    .select('*')
    .eq('user_id', userId)
    .single();

  if (error && error.code !== 'PGRST116') throw error;
  return data;
};

// Reassign review to another staff member
export const reassignReview = async (reviewId, newStaffUserId, assignedBy) => {
  const { data: oldReview } = await supabase
    .from('manual_review_queue')
    .select('assigned_to')
    .eq('id', reviewId)
    .single();

  const { data, error } = await supabase
    .from('manual_review_queue')
    .update({
      assigned_to: newStaffUserId,
      assigned_by: assignedBy,
      status: 'assigned'
    })
    .eq('id', reviewId)
    .select()
    .single();

  if (error) throw error;

  // CT-FINAL-03: the 'reassigned' audit INSERT that used to run here was removed.

  return data;
};