import api from './api';

export const activityCommentService = {
  // Get comments for an activity
  async getActivityComments(activityType, activityUserId, itemId) {
    const response = await api.get('/api/activity-comments/', {
      params: {
        activity_type: activityType,
        activity_user_id: activityUserId,
        item_id: itemId
      }
    });
    return response.data;
  },

  // Create a comment or reply
  async createComment(activityType, activityUserId, itemId, content, parentCommentId = null) {
    const response = await api.post('/api/activity-comments/', {
      activity_type: activityType,
      activity_user_id: activityUserId,
      item_id: itemId,
      content: content,
      parent_comment_id: parentCommentId
    });
    return response.data;
  },

  // Delete a comment
  async deleteComment(commentId) {
    const response = await api.delete(`/api/activity-comments/${commentId}`);
    return response.data;
  }
};
