import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { userService } from '../services/userService';
import { authService } from '../services/authService';
import Navbar from '../components/common/Navbar';

export default function Settings() {
  const { user, updateUser } = useAuth();
  const { language } = useLanguage();
  const navigate = useNavigate();

  // Profile editing state
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState({
    display_name: user?.display_name || '',
    email: user?.email || ''
  });
  const [profileError, setProfileError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');

  // Password changing state
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // Avatar changing state
  const [isChangingAvatar, setIsChangingAvatar] = useState(false);
  const [avatarMode, setAvatarMode] = useState('upload'); // 'upload' or 'character'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [fiveStarCharacters, setFiveStarCharacters] = useState([]);
  const [selectedCharacterId, setSelectedCharacterId] = useState(null);
  const [avatarError, setAvatarError] = useState('');
  const [avatarSuccess, setAvatarSuccess] = useState('');
  const [loadingCharacters, setLoadingCharacters] = useState(false);

  const handleProfileEdit = () => {
    setIsEditingProfile(true);
    setProfileData({
      display_name: user?.display_name || '',
      email: user?.email || ''
    });
    setProfileError('');
    setProfileSuccess('');
  };

  const handleProfileCancel = () => {
    setIsEditingProfile(false);
    setProfileData({
      display_name: user?.display_name || '',
      email: user?.email || ''
    });
    setProfileError('');
  };

  const handleProfileSave = async () => {
    try {
      setProfileError('');
      setProfileSuccess('');

      await userService.updateProfile({
        display_name: profileData.display_name,
        email: profileData.email
      });

      // Fetch latest user data from API to ensure all fields are correct
      const updatedUser = await authService.getCurrentUser();
      updateUser(updatedUser);

      setIsEditingProfile(false);
      setProfileSuccess(language === 'ko' ? '프로필이 업데이트되었습니다.' : 'Profile updated successfully.');
      setTimeout(() => setProfileSuccess(''), 3000);
    } catch (err) {
      console.error('Failed to update profile:', err);
      setProfileError(
        language === 'ko'
          ? err.response?.data?.detail || '프로필 업데이트에 실패했습니다.'
          : err.response?.data?.detail || 'Failed to update profile.'
      );
    }
  };

  const handlePasswordChange = () => {
    setIsChangingPassword(true);
    setPasswordData({
      current_password: '',
      new_password: '',
      confirm_password: ''
    });
    setPasswordError('');
    setPasswordSuccess('');
  };

  const handlePasswordCancel = () => {
    setIsChangingPassword(false);
    setPasswordData({
      current_password: '',
      new_password: '',
      confirm_password: ''
    });
    setPasswordError('');
  };

  const handlePasswordSave = async () => {
    try {
      setPasswordError('');
      setPasswordSuccess('');

      // Validate
      if (passwordData.new_password.length < 8) {
        setPasswordError(language === 'ko' ? '새 비밀번호는 최소 8자 이상이어야 합니다.' : 'New password must be at least 8 characters.');
        return;
      }

      if (passwordData.new_password !== passwordData.confirm_password) {
        setPasswordError(language === 'ko' ? '새 비밀번호가 일치하지 않습니다.' : 'New passwords do not match.');
        return;
      }

      await userService.updatePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });

      setIsChangingPassword(false);
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      setPasswordSuccess(language === 'ko' ? '비밀번호가 변경되었습니다.' : 'Password changed successfully.');
      setTimeout(() => setPasswordSuccess(''), 3000);
    } catch (err) {
      console.error('Failed to change password:', err);
      setPasswordError(
        language === 'ko'
          ? err.response?.data?.detail || '비밀번호 변경에 실패했습니다.'
          : err.response?.data?.detail || 'Failed to change password.'
      );
    }
  };

  const handleAvatarChange = async () => {
    setIsChangingAvatar(true);
    setAvatarError('');
    setAvatarSuccess('');
    setAvatarMode('upload');
    setSelectedFile(null);
    setPreviewUrl(null);
    setSelectedCharacterId(null);

    // Load 5-star characters
    if (avatarMode === 'character' || fiveStarCharacters.length === 0) {
      try {
        setLoadingCharacters(true);
        const characters = await userService.getFiveStarCharacters();
        setFiveStarCharacters(characters);
      } catch (err) {
        console.error('Failed to load characters:', err);
        setAvatarError(language === 'ko' ? '캐릭터 목록을 불러오지 못했습니다.' : 'Failed to load characters.');
      } finally {
        setLoadingCharacters(false);
      }
    }
  };

  const handleAvatarCancel = () => {
    setIsChangingAvatar(false);
    setSelectedFile(null);
    setPreviewUrl(null);
    setSelectedCharacterId(null);
    setAvatarError('');
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        setAvatarError(language === 'ko' ? '지원되지 않는 파일 형식입니다.' : 'Unsupported file type.');
        return;
      }

      // Validate file size (5MB max)
      if (file.size > 5 * 1024 * 1024) {
        setAvatarError(language === 'ko' ? '파일 크기는 5MB 이하여야 합니다.' : 'File size must be less than 5MB.');
        return;
      }

      setSelectedFile(file);
      setAvatarError('');

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAvatarSave = async () => {
    try {
      setAvatarError('');
      setAvatarSuccess('');

      if (avatarMode === 'upload') {
        if (!selectedFile) {
          setAvatarError(language === 'ko' ? '파일을 선택해주세요.' : 'Please select a file.');
          return;
        }

        await userService.uploadAvatar(selectedFile);

      } else if (avatarMode === 'character') {
        if (!selectedCharacterId) {
          setAvatarError(language === 'ko' ? '캐릭터를 선택해주세요.' : 'Please select a character.');
          return;
        }

        await userService.setAvatarFromCharacter(selectedCharacterId);
      }

      // Fetch latest user data from API to ensure all fields are correct
      const updatedUser = await authService.getCurrentUser();
      updateUser(updatedUser);

      setIsChangingAvatar(false);
      setSelectedFile(null);
      setPreviewUrl(null);
      setSelectedCharacterId(null);
      setAvatarSuccess(language === 'ko' ? '프로필 사진이 변경되었습니다.' : 'Profile picture changed successfully.');
      setTimeout(() => setAvatarSuccess(''), 3000);
    } catch (err) {
      console.error('Failed to change avatar:', err);
      setAvatarError(
        language === 'ko'
          ? err.response?.data?.detail || '프로필 사진 변경에 실패했습니다.'
          : err.response?.data?.detail || 'Failed to change profile picture.'
      );
    }
  };

  const getAvatarUrl = (url) => {
    if (!url) return '/placeholder-avatar.png';
    if (url.startsWith('http')) return url;
    return `http://localhost:8000${url}`;
  };

  return (
    <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">

        {/* Settings Sections */}
        <div className="space-y-6">
          {/* Profile Picture Section */}
          <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">
                {language === 'ko' ? '프로필 사진' : 'Profile Picture'}
              </h2>
              {!isChangingAvatar && (
                <button
                  onClick={handleAvatarChange}
                  className="text-sm text-[#3498DB] hover:text-blue-700 font-medium"
                >
                  {language === 'ko' ? '변경' : 'Change'}
                </button>
              )}
            </div>

            {avatarSuccess && (
              <div className="mb-4 p-3 bg-green-100 border border-green-300 text-green-800 rounded-md text-sm">
                {avatarSuccess}
              </div>
            )}

            {avatarError && (
              <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
                {avatarError}
              </div>
            )}

            {!isChangingAvatar ? (
              <div className="flex items-center gap-4">
                {user?.avatar_url ? (
                  <img
                    src={getAvatarUrl(user.avatar_url)}
                    alt="Profile"
                    className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                    onError={(e) => {
                      e.target.src = '';
                      e.target.style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full gradient-custom-profile flex items-center justify-center border-2 border-gray-200">
                    <span className="text-white text-3xl font-bold">
                      {(user?.display_name || user?.username || '?').charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
                <p className="text-sm text-gray-600">
                  {language === 'ko'
                    ? '프로필 사진을 변경하려면 변경 버튼을 클릭하세요.'
                    : 'Click the change button to update your profile picture.'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Mode selector */}
                <div className="flex gap-2 border-b border-gray-200">
                  <button
                    onClick={() => setAvatarMode('upload')}
                    className={`px-4 py-2 font-medium transition-colors ${
                      avatarMode === 'upload'
                        ? 'text-[#3498DB] border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    {language === 'ko' ? '파일 업로드' : 'Upload File'}
                  </button>
                  <button
                    onClick={() => setAvatarMode('character')}
                    className={`px-4 py-2 font-medium transition-colors ${
                      avatarMode === 'character'
                        ? 'text-[#3498DB] border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    {language === 'ko' ? '5점 캐릭터 선택' : 'Select 5-Star Character'}
                  </button>
                </div>

                {/* Upload mode */}
                {avatarMode === 'upload' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {language === 'ko' ? '이미지 파일 선택 (JPG, PNG, GIF, WebP)' : 'Select Image File (JPG, PNG, GIF, WebP)'}
                    </label>
                    <input
                      type="file"
                      accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                      onChange={handleFileSelect}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                    {previewUrl && (
                      <div className="mt-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">
                          {language === 'ko' ? '미리보기' : 'Preview'}
                        </p>
                        <img
                          src={previewUrl}
                          alt="Preview"
                          className="w-32 h-32 rounded-full object-cover border-2 border-gray-200"
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Character selection mode */}
                {avatarMode === 'character' && (
                  <div>
                    {loadingCharacters ? (
                      <p className="text-sm text-gray-600">
                        {language === 'ko' ? '로딩 중...' : 'Loading...'}
                      </p>
                    ) : fiveStarCharacters.length === 0 ? (
                      <p className="text-sm text-gray-600">
                        {language === 'ko'
                          ? '5점 평가한 캐릭터가 없습니다. 캐릭터를 평가해보세요!'
                          : 'No 5-star rated characters. Rate some characters first!'}
                      </p>
                    ) : (
                      <>
                        <p className="text-sm font-medium text-gray-700 mb-3">
                          {language === 'ko' ? '5점 준 캐릭터 중에서 선택하세요' : 'Choose from your 5-star rated characters'}
                        </p>
                        <div className="grid grid-cols-4 gap-3 max-h-96 overflow-y-auto">
                          {fiveStarCharacters.map((char) => (
                            <button
                              key={char.character_id}
                              onClick={() => setSelectedCharacterId(char.character_id)}
                              className={`flex flex-col items-center p-2 rounded-lg border-2 transition-all ${
                                selectedCharacterId === char.character_id
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-gray-200 hover:border-gray-300'
                              }`}
                            >
                              <img
                                src={getAvatarUrl(char.image_url)}
                                alt={char.name_full}
                                className="w-20 h-20 rounded-full object-cover mb-2"
                                onError={(e) => {
                                  e.target.src = '/placeholder-avatar.png';
                                }}
                              />
                              <span className="text-xs text-center line-clamp-2">
                                {char.name_full}
                              </span>
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={handleAvatarSave}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
                  >
                    {language === 'ko' ? '저장' : 'Save'}
                  </button>
                  <button
                    onClick={handleAvatarCancel}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors font-medium"
                  >
                    {language === 'ko' ? '취소' : 'Cancel'}
                  </button>
                </div>
              </div>
            )}
          </div>
          {/* Profile Picture Section */}
          <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">
                {language === 'ko' ? '프로필 정보' : 'Profile Information'}
              </h2>
              {!isEditingProfile && (
                <button
                  onClick={handleProfileEdit}
                  className="text-sm text-[#3498DB] hover:text-blue-700 font-medium"
                >
                  {language === 'ko' ? '편집' : 'Edit'}
                </button>
              )}
            </div>

            {profileSuccess && (
              <div className="mb-4 p-3 bg-green-100 border border-green-300 text-green-800 rounded-md text-sm">
                {profileSuccess}
              </div>
            )}

            {profileError && (
              <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
                {profileError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'ko' ? '사용자명' : 'Username'}
                </label>
                <input
                  type="text"
                  value={user?.username || ''}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {language === 'ko' ? '사용자명은 변경할 수 없습니다.' : 'Username cannot be changed.'}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'ko' ? '이메일' : 'Email'}
                </label>
                <input
                  type="email"
                  value={isEditingProfile ? profileData.email : (user?.email || '')}
                  disabled={!isEditingProfile}
                  onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md ${
                    isEditingProfile ? 'bg-white text-gray-900' : 'bg-gray-50 text-gray-500'
                  }`}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {language === 'ko' ? '표시 이름' : 'Display Name'}
                </label>
                <input
                  type="text"
                  value={isEditingProfile ? profileData.display_name : (user?.display_name || '')}
                  disabled={!isEditingProfile}
                  onChange={(e) => setProfileData({ ...profileData, display_name: e.target.value })}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md ${
                    isEditingProfile ? 'bg-white text-gray-900' : 'bg-gray-50 text-gray-500'
                  }`}
                />
              </div>

              {isEditingProfile && (
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={handleProfileSave}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
                  >
                    {language === 'ko' ? '저장' : 'Save'}
                  </button>
                  <button
                    onClick={handleProfileCancel}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors font-medium"
                  >
                    {language === 'ko' ? '취소' : 'Cancel'}
                  </button>
                </div>
              )}
            </div>
          </div>


          {/* Password Section */}
          <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">
                {language === 'ko' ? '비밀번호' : 'Password'}
              </h2>
              {!isChangingPassword && (
                <button
                  onClick={handlePasswordChange}
                  className="text-sm text-[#3498DB] hover:text-blue-700 font-medium"
                >
                  {language === 'ko' ? '변경' : 'Change'}
                </button>
              )}
            </div>

            {passwordSuccess && (
              <div className="mb-4 p-3 bg-green-100 border border-green-300 text-green-800 rounded-md text-sm">
                {passwordSuccess}
              </div>
            )}

            {passwordError && (
              <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
                {passwordError}
              </div>
            )}

            {!isChangingPassword ? (
              <p className="text-sm text-gray-600">
                {language === 'ko' ? '보안을 위해 정기적으로 비밀번호를 변경하세요.' : 'Change your password regularly for security.'}
              </p>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'ko' ? '현재 비밀번호' : 'Current Password'}
                  </label>
                  <input
                    type="password"
                    value={passwordData.current_password}
                    onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'ko' ? '새 비밀번호' : 'New Password'}
                  </label>
                  <input
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {language === 'ko' ? '최소 8자 이상' : 'At least 8 characters'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {language === 'ko' ? '새 비밀번호 확인' : 'Confirm New Password'}
                  </label>
                  <input
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={handlePasswordSave}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
                  >
                    {language === 'ko' ? '저장' : 'Save'}
                  </button>
                  <button
                    onClick={handlePasswordCancel}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors font-medium"
                  >
                    {language === 'ko' ? '취소' : 'Cancel'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Language Section */}
          <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
            <h2 className="text-xl font-bold mb-4">
              {language === 'ko' ? '언어 설정' : 'Language Settings'}
            </h2>
            <p className="text-gray-600 mb-4">
              {language === 'ko'
                ? '언어는 상단 네비게이션 바에서 변경할 수 있습니다.'
                : 'Language can be changed from the top navigation bar.'}
            </p>
            <div className="flex items-center gap-2 text-sm">
              <span className="font-medium">{language === 'ko' ? '현재 언어:' : 'Current Language:'}</span>
              <span className="text-[#3498DB]">
                {language === 'ko' ? '🇰🇷 한국어' : '🇺🇸 English'}
              </span>
            </div>
          </div>

          {/* About Section */}
          <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
            <h2 className="text-xl font-bold mb-4">
              {language === 'ko' ? '애플리케이션 정보' : 'About'}
            </h2>
            <div className="space-y-2 text-sm text-gray-600">
              <p>
                <span className="font-medium">AniPass</span> - {language === 'ko' ? '애니메이션 평가 플랫폼' : 'Anime Rating Platform'}
              </p>
              <p>Version 1.0.0</p>
              <p className="mt-4">
                {language === 'ko'
                  ? '애니메이션을 평가하고, 캐릭터를 평가하며, 나만의 애니메이션 취향을 발견하세요.'
                  : 'Rate anime, rate characters, and discover your anime taste.'}
              </p>
            </div>
          </div>
        </div>

        {/* Back Button */}
        <div className="mt-8">
          <button
            onClick={() => navigate(-1)}
            className="text-[#3498DB] hover:text-blue-700 font-medium"
          >
            ← {language === 'ko' ? '뒤로 가기' : 'Go Back'}
          </button>
        </div>
      </div>
    </div>
  );
}
