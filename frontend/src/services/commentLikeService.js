import api from './api';

export const commentLikeService = {
  // Toggle like on comment
  async toggleLike(commentId) {
    const response = await api.post('/api/comment-likes/', {
      comment_id: commentId
    });
    return response.data;
  },

  // Check if comment is liked
  async checkLike(commentId) {
    const response = await api.get(`/api/comment-likes/check/${commentId}`);
    return response.data;
  },

  // Get list of users who liked the comment
  async getLikes(commentId) {
    const response = await api.get(`/api/comment-likes/list/${commentId}`);
    return response.data;
  }
};
