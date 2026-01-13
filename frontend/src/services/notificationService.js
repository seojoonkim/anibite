import api from './api';

export const notificationService = {
  /**
   * 알림 목록 가져오기
   */
  async getNotifications(limit = 50, offset = 0) {
    try {
      const response = await api.get('/api/notifications', {
        params: { limit, offset }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get notifications:', error);
      throw error;
    }
  },

  /**
   * 최근 알림 가져오기 (드롭다운용)
   */
  async getRecentNotifications(limit = 5) {
    try {
      const response = await api.get('/api/notifications', {
        params: { limit, offset: 0 }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get recent notifications:', error);
      throw error;
    }
  },

  /**
   * 읽지 않은 알림 개수 가져오기
   */
  async getUnreadCount() {
    try {
      const response = await api.get('/api/notifications/unread-count');
      return response.data.count || 0;
    } catch (error) {
      console.error('Failed to get unread count:', error);
      return 0;
    }
  },

  /**
   * 알림을 읽음 처리 (모두 읽음)
   */
  async markAsRead() {
    try {
      await api.post('/api/notifications/mark-read');
    } catch (error) {
      console.error('Failed to mark notifications as read:', error);
    }
  },

  /**
   * 모든 알림을 읽음 처리 (markAsRead와 동일, 명확성을 위한 alias)
   */
  async markAllAsRead() {
    return this.markAsRead();
  }
};
