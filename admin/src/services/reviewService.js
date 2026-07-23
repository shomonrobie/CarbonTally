// D:\carbon_ledger\admin\src\services\reviewService.js
import { supabase } from '../supabaseClient';

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

  // Create audit trail entry
  await supabase
    .from('review_audit_trail')
    .insert({
      review_id: reviewId,
      action: 'assigned',
      performed_by: assignedBy,
      assigned_to: staffUserId,
      new_value: { assigned_to: staffUserId }
    });

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

  await supabase
    .from('review_audit_trail')
    .insert({
      review_id: reviewId,
      action: 'started',
      performed_by: staffUserId
    });

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

  // Create audit trail
  await supabase
    .from('review_audit_trail')
    .insert({
      review_id: reviewId,
      action: 'completed',
      performed_by: staffUserId,
      new_value: { data_entry: dataEntry }
    });

  return data;
};

// Get review audit trail
export const getReviewAuditTrail = async (reviewId) => {
  const { data, error } = await supabase
    .from('review_audit_trail')
    .select(`
      *,
      performer:performed_by (email),
      assignee:assigned_to (email)
    `)
    .eq('review_id', reviewId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data || [];
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

  await supabase
    .from('review_audit_trail')
    .insert({
      review_id: reviewId,
      action: 'reassigned',
      performed_by: assignedBy,
      assigned_to: newStaffUserId,
      old_value: { assigned_to: oldReview?.assigned_to },
      new_value: { assigned_to: newStaffUserId }
    });

  return data;
};