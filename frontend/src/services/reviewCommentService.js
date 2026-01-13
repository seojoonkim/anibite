import api from './api';

export const reviewCommentService = {
  // Get comments for a review
  async getReviewComments(reviewId, reviewType = 'anime') {
    const response = await api.get(`/api/comments/review/${reviewId}`, {
      params: { review_type: reviewType }
    });
    return response.data;
  },

  // Create a comment on a review
  async createReviewComment(reviewId, data) {
    const response = await api.post('/api/comments/', {
      review_id: reviewId,
      review_type: 'anime',
      content: data.content,
      parent_comment_id: data.parent_comment_id || null
    });
    return response.data;
  },

  // Create a comment with review_type parameter
  async createComment(data) {
    const response = await api.post('/api/comments/', {
      review_id: data.review_id,
      review_type: data.review_type || 'anime',
      content: data.content,
      parent_comment_id: data.parent_comment_id || null
    });
    return response.data;
  },

  // Create a reply to a comment
  async createReply(parentCommentId, data) {
    // Get parent comment to determine review_id
    const response = await api.post('/api/comments/', {
      review_id: data.review_id,
      review_type: data.review_type || 'character',
      content: data.content,
      parent_comment_id: parentCommentId
    });
    return response.data;
  },

  // Delete a comment
  async deleteReviewComment(commentId) {
    const response = await api.delete(`/api/comments/${commentId}`);
    return response.data;
  },

  // Like a comment
  async likeReviewComment(commentId) {
    const response = await api.post(`/api/comments/${commentId}/like`);
    return response.data;
  },

  // Unlike a comment
  async unlikeReviewComment(commentId) {
    const response = await api.delete(`/api/comments/${commentId}/like`);
    return response.data;
  },
};
