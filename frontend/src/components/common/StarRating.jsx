import { useState, useRef, useEffect } from 'react';

export default function StarRating({ rating, onRatingChange, readonly = false, size = 'md', showNumber = true, align = 'left', dynamicSize = false }) {
  const [hoverRating, setHoverRating] = useState(0);
  const containerRef = useRef(null);
  const [computedSize, setComputedSize] = useState(null);

  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-4xl sm:text-5xl',
    xl: 'text-6xl',
  };

  useEffect(() => {
    if (dynamicSize && containerRef.current) {
      const updateSize = () => {
        // 부모 컨테이너의 너비를 직접 사용
        const parentElement = containerRef.current.parentElement;
        if (parentElement) {
          const containerWidth = parentElement.offsetWidth;
          // 별 5개 + gap을 고려한 크기 계산
          // 패딩과 여백을 고려하여 65%만 사용
          const availableWidth = containerWidth * 0.65;
          const singleStarSize = availableWidth / 6.5; // 더 보수적으로
          setComputedSize(`${singleStarSize}px`);
        }
      };

      // DOM이 완전히 렌더링된 후 실행
      setTimeout(updateSize, 150);
      window.addEventListener('resize', updateSize);
      return () => window.removeEventListener('resize', updateSize);
    }
  }, [dynamicSize]);

  const getStarType = (position) => {
    // Only show hover effect if hovering and it's different from current rating
    const currentRating = readonly ? rating : (hoverRating > 0 ? hoverRating : rating);
    if (currentRating >= position) {
      return 'full';
    } else if (currentRating >= position - 0.5) {
      return 'half';
    }
    return 'empty';
  };

  const handleClick = (e, position) => {
    if (readonly || !onRatingChange) return;

    // Detect click position (left half or right half)
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const isLeftHalf = x < rect.width / 2;
    const clickedRating = isLeftHalf ? position - 0.5 : position;

    // If clicking the same rating, set to 0 (remove rating)
    if (rating === clickedRating) {
      onRatingChange(0);
    } else {
      onRatingChange(clickedRating);
    }
  };

  const handleMouseMove = (e, position) => {
    if (readonly || !onRatingChange) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const isLeftHalf = x < rect.width / 2;

    setHoverRating(isLeftHalf ? position - 0.5 : position);
  };

  const StarIcon = ({ type }) => {
    const gradientStyle = {
      background: 'linear-gradient(135deg, #833AB4 0%, #E1306C 40%, #F77737 70%, #FCAF45 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text'
    };

    if (type === 'full') {
      return <span style={gradientStyle}>★</span>;
    } else if (type === 'half') {
      return (
        <span className="relative inline-block">
          <span className="text-gray-300">★</span>
          <span className="absolute top-0 left-0 overflow-hidden w-1/2" style={gradientStyle}>
            ★
          </span>
        </span>
      );
    }
    return <span className="text-gray-300">★</span>;
  };

  const gapClasses = {
    sm: 'gap-0.5',
    md: 'gap-1',
    lg: 'gap-1 sm:gap-1.5',
    xl: 'gap-0',
  };

  const alignClasses = {
    left: '',
    center: 'justify-center'
  };

  const finalSize = dynamicSize && computedSize ? computedSize : null;
  const sizeClass = finalSize ? '' : sizeClasses[size];

  return (
    <div
      className={`flex items-center ${alignClasses[align]}`}
      ref={containerRef}
      onMouseLeave={() => setHoverRating(0)}
    >
      <div
        className={`flex items-center ${gapClasses[size]} ${sizeClass}`}
        style={finalSize ? { fontSize: finalSize } : {}}
      >
        {[1, 2, 3, 4, 5].map((position) => (
          <button
            key={position}
            type="button"
            onClick={(e) => handleClick(e, position)}
            onMouseMove={(e) => handleMouseMove(e, position)}
            disabled={readonly}
            className={`${sizeClasses[size]} ${
              readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110'
            } transition-transform`}
          >
            <StarIcon type={getStarType(position)} />
          </button>
        ))}
      </div>
      {showNumber && rating > 0 && (
        <span className="ml-2 text-gray-700 font-medium">{rating.toFixed(1)}</span>
      )}
    </div>
  );
}
