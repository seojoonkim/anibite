import { useState, useCallback, useEffect } from 'react';
import Cropper from 'react-easy-crop';
import imageCompression from 'browser-image-compression';

export default function ImageCropModal({ imageFile, onComplete, onCancel, aspectRatio = 3/4 }) {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(0.5);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState(null);
  const [imageSrc, setImageSrc] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // 이미지 파일을 Data URL로 변환
  useEffect(() => {
    if (imageFile) {
      const reader = new FileReader();
      reader.onload = () => setImageSrc(reader.result);
      reader.readAsDataURL(imageFile);
    }
  }, [imageFile]);

  const onCropComplete = useCallback((croppedArea, croppedAreaPixels) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const createCroppedImage = async () => {
    if (!imageSrc || !croppedAreaPixels) return;

    setIsProcessing(true);

    try {
      const image = await createImage(imageSrc);
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      // 목표 크기: 최대 400x533 (3:4 비율)
      const maxWidth = 400;
      const maxHeight = 533;

      let targetWidth = croppedAreaPixels.width;
      let targetHeight = croppedAreaPixels.height;

      // 너무 크면 리사이즈
      if (targetWidth > maxWidth || targetHeight > maxHeight) {
        const scale = Math.min(maxWidth / targetWidth, maxHeight / targetHeight);
        targetWidth = Math.round(targetWidth * scale);
        targetHeight = Math.round(targetHeight * scale);
      }

      canvas.width = targetWidth;
      canvas.height = targetHeight;

      ctx.drawImage(
        image,
        croppedAreaPixels.x,
        croppedAreaPixels.y,
        croppedAreaPixels.width,
        croppedAreaPixels.height,
        0,
        0,
        targetWidth,
        targetHeight
      );

      // Canvas를 Blob으로 변환
      const blob = await new Promise((resolve) => {
        canvas.toBlob(resolve, 'image/jpeg', 0.92);
      });

      // 압축
      const compressedFile = await imageCompression(blob, {
        maxSizeMB: 0.2, // 최대 200KB
        maxWidthOrHeight: 400,
        useWebWorker: true,
        fileType: 'image/jpeg'
      });

      // File 객체로 변환
      const finalFile = new File(
        [compressedFile],
        imageFile.name.replace(/\.[^/.]+$/, '.jpg'),
        { type: 'image/jpeg' }
      );

      onComplete(finalFile);
    } catch (error) {
      console.error('이미지 처리 실패:', error);
      alert('이미지 처리에 실패했습니다.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4">
        <h2 className="text-2xl font-bold mb-4 text-white">이미지 크롭 (3:4 비율)</h2>

        <div className="relative h-96 bg-gray-900 rounded mb-4">
          {imageSrc && (
            <Cropper
              image={imageSrc}
              crop={crop}
              zoom={zoom}
              aspect={aspectRatio}
              minZoom={0.1}
              maxZoom={3}
              onCropChange={setCrop}
              onZoomChange={setZoom}
              onCropComplete={onCropComplete}
              restrictPosition={true}
            />
          )}
        </div>

        <div className="mb-4">
          <label className="block text-sm text-gray-300 mb-2">
            확대/축소: {Math.round(zoom * 100)}%
          </label>
          <input
            type="range"
            min={0.1}
            max={3}
            step={0.05}
            value={zoom}
            onChange={(e) => setZoom(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>축소</span>
            <span>확대</span>
          </div>
        </div>

        <div className="text-sm text-gray-400 mb-4">
          <p>• 최종 크기: 최대 400×533px</p>
          <p>• 파일 형식: JPEG (자동 변환)</p>
          <p>• 최대 용량: 200KB (자동 압축)</p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={createCroppedImage}
            disabled={isProcessing}
            className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold disabled:opacity-50"
          >
            {isProcessing ? '처리 중...' : '완료'}
          </button>
          <button
            onClick={onCancel}
            disabled={isProcessing}
            className="flex-1 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold disabled:opacity-50"
          >
            취소
          </button>
        </div>
      </div>
    </div>
  );
}

// 헬퍼 함수: 이미지 로드
const createImage = (url) =>
  new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener('load', () => resolve(image));
    image.addEventListener('error', (error) => reject(error));
    image.src = url;
  });
