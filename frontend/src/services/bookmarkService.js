/**
 * Bookmark Service
 * 서버 기반 북마크 관리
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get all bookmarks for current user
export const getBookmarks = async (full = false) => {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const url = `${API_BASE_URL}/api/bookmarks/${full ? '?full=true' : ''}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch bookmarks');
  }

  const data = await response.json();
  return full ? data : (data.bookmarks || []);
};

// Add bookmark
export const addBookmark = async (activityId) => {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_BASE_URL}/api/bookmarks/${activityId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to add bookmark');
  }

  return response.json();
};

// Remove bookmark
export const removeBookmark = async (activityId) => {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_BASE_URL}/api/bookmarks/${activityId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to remove bookmark');
  }

  return response.json();
};

// Check if activity is bookmarked
export const checkBookmark = async (activityId) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/bookmarks/check/${activityId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.bookmarked || false;
  } catch (error) {
    console.error('Failed to check bookmark:', error);
    return false;
  }
};

// Migrate localStorage bookmarks to server
export const migrateLocalBookmarks = async () => {
  try {
    const localBookmarks = JSON.parse(localStorage.getItem('anipass_bookmarks') || '[]');

    if (localBookmarks.length === 0) {
      return { migrated: 0 };
    }

    console.log(`Migrating ${localBookmarks.length} bookmarks to server...`);

    let migrated = 0;
    for (const activityId of localBookmarks) {
      try {
        await addBookmark(activityId);
        migrated++;
      } catch (error) {
        console.error(`Failed to migrate bookmark ${activityId}:`, error);
      }
    }

    // Clear localStorage after migration
    if (migrated > 0) {
      localStorage.removeItem('anipass_bookmarks');
      console.log(`✅ Migrated ${migrated} bookmarks to server`);
    }

    return { migrated };
  } catch (error) {
    console.error('Failed to migrate bookmarks:', error);
    return { migrated: 0 };
  }
};

export const bookmarkService = {
  getBookmarks,
  addBookmark,
  removeBookmark,
  checkBookmark,
  migrateLocalBookmarks,
};

export default bookmarkService;
