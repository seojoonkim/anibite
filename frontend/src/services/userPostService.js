import api from './api';

export const userPostService = {
  // Create a new post
  async createPost(content) {
    const response = await api.post('/api/user-posts/', {
      content: content
    });
    return response.data;
  },

  // Get a specific post
  async getPost(postId) {
    const response = await api.get(`/api/user-posts/${postId}`);
    return response.data;
  },

  // Update a post
  async updatePost(postId, content) {
    const response = await api.put(`/api/user-posts/${postId}`, {
      content: content
    });
    return response.data;
  },

  // Delete a post
  async deletePost(postId) {
    const response = await api.delete(`/api/user-posts/${postId}`);
    return response.data;
  },

  // Get posts by user
  async getUserPosts(userId, limit = 50, offset = 0) {
    const response = await api.get(`/api/user-posts/user/${userId}`, {
      params: { limit, offset }
    });
    return response.data;
  }
};
