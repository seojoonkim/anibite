import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import ImageCropModal from '../components/ImageCropModal';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 이미지 URL 처리 헬퍼 함수 (어드민용 - 항상 캐시 우회)
const getImageUrl = (imagePath, itemId = null, type = 'anime') => {
  if (!imagePath) {
    // 이미지 경로가 없으면 ID로 직접 시도
    if (itemId && type === 'character') {
      return `${API_BASE_URL}/api/images/characters/${itemId}.jpg?v=${Date.now()}`;
    }
    return null;
  }

  let url;

  // AniList character URL - use auto-download API
  if (imagePath.startsWith('http') && imagePath.includes('anilist.co') && imagePath.includes('/character/')) {
    // Extract character ID from AniList URL
    const match = imagePath.match(/\/b(\d+)-/);
    if (match && match[1]) {
      const extractedId = match[1];
      url = `${API_BASE_URL}/api/images/characters/${extractedId}.jpg`;
    } else if (itemId) {
      // Use provided character ID
      url = `${API_BASE_URL}/api/images/characters/${itemId}.jpg`;
    } else {
      // Fallback to direct URL
      url = imagePath;
    }
  } else if (imagePath.startsWith('http')) {
    // Other HTTP URLs (R2, etc.)
    url = imagePath;
  } else if (imagePath.startsWith('/')) {
    url = `${API_BASE_URL}${imagePath}`;
  } else {
    url = `${API_BASE_URL}/${imagePath}`;
  }

  // 어드민 에디터는 항상 최신 이미지를 보여야 하므로 캐시 우회
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}v=${Date.now()}`;
};

export default function AdminEditor() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('both');
  const [searchResults, setSearchResults] = useState({ anime: [], characters: [] });
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedType, setSelectedType] = useState(null);
  const [editData, setEditData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [uploadingImage, setUploadingImage] = useState(false);
  const [showCropModal, setShowCropModal] = useState(false);
  const [selectedImageFile, setSelectedImageFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // 검색
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setMessage('');

    try {
      const response = await api.get(
        '/api/admin/editor/search',
        {
          params: { q: searchQuery, type: searchType, limit: 20 }
        }
      );

      setSearchResults(response.data);
    } catch (error) {
      console.error('검색 실패:', error);
      setMessage(error.response?.data?.detail || '검색 실패');
    } finally {
      setIsLoading(false);
    }
  };

  // 항목 선택
  const selectItem = async (id, type) => {
    setIsLoading(true);
    setMessage('');

    try {
      const endpoint = type === 'anime'
        ? `/api/admin/editor/anime/${id}`
        : `/api/admin/editor/character/${id}`;

      const response = await api.get(endpoint);

      setSelectedItem(response.data);
      setSelectedType(type);
      setEditData(response.data);
    } catch (error) {
      console.error('불러오기 실패:', error);
      setMessage(error.response?.data?.detail || '불러오기 실패');
    } finally {
      setIsLoading(false);
    }
  };

  // 이미지 파일 선택 (크롭 모달 표시)
  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 파일 타입 체크
    if (!file.type.startsWith('image/')) {
      setMessage('❌ 이미지 파일만 업로드 가능합니다.');
      return;
    }

    setSelectedImageFile(file);
    setShowCropModal(true);
  };

  // 드래그 앤 드롭 핸들러
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (!file) return;

    // 파일 타입 체크
    if (!file.type.startsWith('image/')) {
      setMessage('❌ 이미지 파일만 업로드 가능합니다.');
      return;
    }

    setSelectedImageFile(file);
    setShowCropModal(true);
  };

  // 크롭 완료 후 업로드
  const handleCropComplete = async (croppedFile) => {
    setShowCropModal(false);
    setUploadingImage(true);
    setMessage('');

    try {
      // 1. 기존 이미지 삭제 (R2에 있는 경우만)
      const imageField = selectedType === 'anime' ? 'cover_image' : 'image_large';
      const oldImageUrl = editData[imageField];

      if (oldImageUrl && oldImageUrl.includes('images.anibite.com')) {
        try {
          await api.delete('/api/admin/editor/delete-image', {
            data: { image_url: oldImageUrl }
          });
        } catch (error) {
          console.warn('기존 이미지 삭제 실패 (무시):', error);
        }
      }

      // 2. 새 이미지 업로드
      const formData = new FormData();
      formData.append('file', croppedFile);

      const response = await api.post(
        `/api/admin/editor/upload-image?type=${selectedType}&item_id=${selectedItem.id}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      // 3. 업로드된 이미지 URL로 업데이트
      const newImageUrl = response.data.url;
      console.log('[Admin Editor] Upload response:', response.data);
      console.log('[Admin Editor] New image URL:', newImageUrl);
      console.log('[Admin Editor] Image field:', imageField);

      setEditData(prev => {
        const updated = { ...prev, [imageField]: newImageUrl };
        console.log('[Admin Editor] Updated editData:', updated);
        return updated;
      });
      setSelectedItem(prev => {
        const updated = { ...prev, [imageField]: newImageUrl };
        console.log('[Admin Editor] Updated selectedItem:', updated);
        return updated;
      });
      setMessage(`✅ 이미지 업로드 완료! (${Math.round(croppedFile.size / 1024)}KB) 저장 버튼을 눌러주세요.`);
    } catch (error) {
      console.error('이미지 업로드 실패:', error);
      setMessage(error.response?.data?.detail || '이미지 업로드 실패');
    } finally {
      setUploadingImage(false);
      setSelectedImageFile(null);
    }
  };

  // 저장
  const handleSave = async () => {
    if (!selectedItem) {
      console.log('[Admin Editor] No item selected');
      return;
    }

    console.log('[Admin Editor] Saving...');
    console.log('[Admin Editor] Selected type:', selectedType);
    console.log('[Admin Editor] Selected item:', selectedItem);
    console.log('[Admin Editor] Edit data:', editData);

    setIsLoading(true);
    setMessage('');

    try {
      const endpoint = selectedType === 'anime'
        ? `/api/admin/editor/anime/${selectedItem.id}`
        : `/api/admin/editor/character/${selectedItem.id}`;

      // 필요한 필드만 추출
      let dataToSend;
      if (selectedType === 'anime') {
        dataToSend = {
          title_korean: editData.title_korean,
          title_romaji: editData.title_romaji,
          title_english: editData.title_english,
          title_native: editData.title_native,
          cover_image: editData.cover_image
        };
      } else {
        dataToSend = {
          name_korean: editData.name_korean,
          name_full: editData.name_full,
          name_native: editData.name_native,
          image_large: editData.image_large
        };
      }

      console.log('[Admin Editor] Endpoint:', endpoint);
      console.log('[Admin Editor] Sending data:', dataToSend);

      const response = await api.patch(endpoint, dataToSend);

      console.log('[Admin Editor] Save response:', response.data);
      setMessage('✅ 저장 완료!');
      // 검색 결과 갱신
      handleSearch({ preventDefault: () => { } });
    } catch (error) {
      console.error('저장 실패:', error);
      console.error('Error response:', error.response?.data);
      setMessage(error.response?.data?.detail || '저장 실패');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-text-primary p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-text-primary">🛠️ Admin Editor</h1>
          <Link
            to="/admin/backup"
            className="px-5 py-2.5 bg-secondary hover:bg-secondary-dark rounded-lg font-semibold transition-colors text-white"
          >
            💾 백업 & 중복 제거
          </Link>
        </div>

        {/* 검색 */}
        <div className="bg-surface rounded-xl border border-border p-6 mb-8">
          <form onSubmit={handleSearch} className="flex gap-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="작품 또는 캐릭터 검색 (모든 언어)"
              className="flex-1 px-4 py-3 bg-input rounded-lg text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary border border-border"
            />

            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              className="px-4 py-3 bg-input rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary border border-border"
            >
              <option value="both">모두</option>
              <option value="anime">작품만</option>
              <option value="character">캐릭터만</option>
            </select>

            <button
              type="submit"
              disabled={isLoading}
              className="px-8 py-3 bg-primary hover:bg-primary-dark rounded-lg font-semibold disabled:opacity-50 text-white transition-colors"
            >
              {isLoading ? '검색 중...' : '검색'}
            </button>
          </form>
        </div>

        {message && (
          <div className={`mb-4 p-4 rounded-lg border ${message.startsWith('✅') ? 'bg-success/20 border-success text-success' : 'bg-error/20 border-error text-error'}`}>
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 검색 결과 */}
          <div className="bg-surface rounded-xl border border-border p-6">
            <h2 className="text-xl font-bold mb-4 text-text-primary">검색 결과</h2>

            {/* 작품 */}
            {searchResults.anime.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-primary">📺 작품 ({searchResults.anime.length})</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {searchResults.anime.map((anime) => (
                    <button
                      key={anime.id}
                      onClick={() => selectItem(anime.id, 'anime')}
                      className={`w-full text-left p-3 rounded-lg transition ${selectedItem?.id === anime.id && selectedType === 'anime'
                        ? 'bg-primary/30 border border-primary'
                        : 'bg-surface-elevated hover:bg-surface-hover border border-transparent'
                        }`}
                    >
                      <div className="flex gap-3">
                        <img
                          src={getImageUrl(anime.cover_image, anime.id, 'anime')}
                          alt={anime.title_korean || anime.title_romaji}
                          className="w-12 h-16 object-cover rounded bg-surface flex-shrink-0"
                          onError={(e) => { e.target.src = '/placeholder-anime.svg'; }}
                        />
                        <div className="min-w-0">
                          <div className="font-semibold text-text-primary truncate">{anime.title_korean || anime.title_romaji}</div>
                          <div className="text-sm text-text-secondary truncate">{anime.title_romaji}</div>
                          <div className="text-xs text-text-tertiary truncate">{anime.title_english}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* 캐릭터 */}
            {searchResults.characters.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3 text-tertiary">👤 캐릭터 ({searchResults.characters.length})</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {searchResults.characters.map((char) => (
                    <button
                      key={char.id}
                      onClick={() => selectItem(char.id, 'character')}
                      className={`w-full text-left p-3 rounded-lg transition ${selectedItem?.id === char.id && selectedType === 'character'
                        ? 'bg-tertiary/30 border border-tertiary'
                        : 'bg-surface-elevated hover:bg-surface-hover border border-transparent'
                        }`}
                    >
                      <div className="flex gap-3">
                        <img
                          src={getImageUrl(char.image_large, char.id, 'character')}
                          alt={char.name_korean || char.name_full}
                          className="w-12 h-16 object-cover rounded bg-surface flex-shrink-0"
                          onError={(e) => { e.target.src = '/placeholder-anime.svg'; }}
                        />
                        <div className="min-w-0">
                          <div className="font-semibold text-text-primary truncate">{char.name_korean || char.name_full}</div>
                          <div className="text-sm text-text-secondary truncate">{char.name_full}</div>
                          <div className="text-xs text-text-tertiary truncate">{char.anime_title}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {searchResults.anime.length === 0 && searchResults.characters.length === 0 && searchQuery && (
              <div className="text-center text-text-tertiary py-8">
                검색 결과가 없습니다
              </div>
            )}
          </div>

          {/* 편집 폼 */}
          <div className="bg-surface rounded-xl border border-border p-6">
            <h2 className="text-xl font-bold mb-4 text-text-primary">편집</h2>

            {selectedItem ? (
              <div className="space-y-6">
                {/* 이미지 미리보기 및 업로드 */}
                <div>
                  <label className="block text-sm font-semibold mb-2 text-text-secondary">
                    {selectedType === 'anime' ? '작품 이미지' : '캐릭터 이미지'}
                  </label>
                  <div className="flex gap-4 items-start">
                    <img
                      src={getImageUrl(selectedType === 'anime' ? editData.cover_image : editData.image_large, selectedItem.id, selectedType)}
                      alt="preview"
                      className="w-24 h-32 object-cover rounded bg-surface-elevated"
                      onError={(e) => { e.target.src = '/placeholder-anime.svg'; }}
                    />
                    <div className="flex-1">
                      {/* 드래그 앤 드롭 영역 */}
                      <div
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${isDragging
                          ? 'border-secondary bg-secondary/10'
                          : 'border-border bg-surface-elevated'
                          } ${uploadingImage ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                      >
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageSelect}
                          disabled={uploadingImage}
                          className="hidden"
                          id="image-upload"
                        />
                        <label
                          htmlFor="image-upload"
                          className="cursor-pointer block"
                        >
                          <div className="text-4xl mb-2">📁</div>
                          <p className="text-sm text-text-secondary mb-1">
                            파일을 여기로 드래그하거나 클릭하세요
                          </p>
                          <p className="text-xs text-text-tertiary">
                            • 3:4 비율로 자동 크롭
                          </p>
                          <p className="text-xs text-text-tertiary">
                            • 최대 400×533px, 200KB로 자동 최적화
                          </p>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 작품 편집 */}
                {selectedType === 'anime' && (
                  <>
                    <div>
                      <label className="block text-sm font-semibold mb-2 text-text-secondary">한국어 제목</label>
                      <input
                        type="text"
                        value={editData.title_korean || ''}
                        onChange={(e) => setEditData({ ...editData, title_korean: e.target.value })}
                        className="w-full px-4 py-3 bg-input rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary border border-border"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold mb-2 text-text-secondary">로마자 제목</label>
                      <input
                        type="text"
                        value={editData.title_romaji || ''}
                        onChange={(e) => setEditData({ ...editData, title_romaji: e.target.value })}
                        className="w-full px-4 py-3 bg-input rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary border border-border"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold mb-2 text-text-secondary">영어 제목</label>
                      <input
                        type="text"
                        value={editData.title_english || ''}
                        onChange={(e) => setEditData({ ...editData, title_english: e.target.value })}
                        className="w-full px-4 py-3 bg-input rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary border border-border"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold mb-2 text-text-secondary">일본어 제목</label>
                      <input
                        type="text"
                        value={editData.title_native || ''}
                        onChange={(e) => setEditData({ ...editData, title_native: e.target.value })}
                        className="w-full px-4 py-3 bg-input rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary border border-border"
                      />
                    </div>
                  </>
                )}

                {/* 캐릭터 편집 */}
                {selectedType === 'character' && (
                  <>
                    {/* 애니메이션 제목 표시 */}
                    {editData.anime_title && (
                      <div className="bg-surface-elevated rounded-lg p-3 mb-4 border border-border">
                        <div className="text-xs text-text-tertiary">작품</div>
                        <div className="text-sm font-semibold text-tertiary">{editData.anime_title}</div>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-semibold mb-2 text-text-secondary">한국어 이름</label>
                      <input
                        type="text"
                        value={editData.name_korean || ''}
                        onChange={(e) => setEditData({ ...editData, name_korean: e.target.value })}
                        className="w-full px-4 py-3 bg-input rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-tertiary border border-border"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold mb-2 text-text-secondary">영어 이름</label>
                      <input
                        type="text"
                        value={editData.name_full || ''}
                        onChange={(e) => setEditData({ ...editData, name_full: e.target.value })}
                        className="w-full px-4 py-3 bg-input rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-tertiary border border-border"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold mb-2 text-text-secondary">일본어 이름</label>
                      <input
                        type="text"
                        value={editData.name_native || ''}
                        onChange={(e) => setEditData({ ...editData, name_native: e.target.value })}
                        className="w-full px-4 py-3 bg-input rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-tertiary border border-border"
                      />
                    </div>
                  </>
                )}

                <button
                  onClick={handleSave}
                  disabled={isLoading}
                  className={`w-full px-6 py-4 rounded-lg font-bold text-lg text-white ${selectedType === 'anime'
                    ? 'bg-primary hover:bg-primary-dark'
                    : 'bg-tertiary hover:bg-tertiary-dark'
                    } disabled:opacity-50 transition`}
                >
                  {isLoading ? '저장 중...' : '💾 저장'}
                </button>
              </div>
            ) : (
              <div className="text-center text-text-tertiary py-16">
                ← 왼쪽에서 항목을 선택하세요
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 이미지 크롭 모달 */}
      {showCropModal && selectedImageFile && (
        <ImageCropModal
          imageFile={selectedImageFile}
          onComplete={handleCropComplete}
          onCancel={() => {
            setShowCropModal(false);
            setSelectedImageFile(null);
          }}
          aspectRatio={3 / 4}
        />
      )}
    </div>
  );
}
