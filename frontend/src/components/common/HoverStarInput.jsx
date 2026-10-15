import { useState } from 'react';

const STAR_PATH = 'M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z';

export function Star({ fill }) {
  return (
    <span className="relative block h-full w-full" aria-hidden="true">
      <svg className="absolute inset-0 h-full w-full text-white/40" fill="currentColor" viewBox="0 0 20 20"><path d={STAR_PATH} /></svg>
      {fill > 0 && (
        <span className="absolute inset-y-0 left-0 overflow-hidden" style={{ width: `${fill * 100}%` }}>
          <svg className="h-full text-[#F5C842]" style={{ width: `${100 / fill}%`, maxWidth: 'none' }} fill="currentColor" viewBox="0 0 20 20"><path d={STAR_PATH} /></svg>
        </span>
      )}
    </span>
  );
}

const fillFor = (value, position) => Math.max(0, Math.min(1, value - (position - 1)));

export function StarRow({ value, size = '2.25rem' }) {
  return (
    <span className="flex justify-center" role="img" aria-label={`5점 만점에 ${value}점`}>
      {[1, 2, 3, 4, 5].map(p => <span key={p} style={{ width: size, height: size }}><Star fill={fillFor(value, p)} /></span>)}
    </span>
  );
}

/** Clickable 5-star input with half-star precision on hover (same behaviour as character cards). */
export default function HoverStarInput({ value = 0, onChange, size = '2.25rem', disabled = false, language = 'ko' }) {
  const [hover, setHover] = useState(0);
  const shown = hover || value;
  const pick = (event, position) => {
    const rect = event.currentTarget.getBoundingClientRect();
    return event.clientX - rect.left < rect.width / 2 ? position - 0.5 : position;
  };
  return (
    <div className="flex justify-center" onMouseLeave={() => setHover(0)} role="group" aria-label={language === 'ko' ? '별점 주기' : 'Rate'}>
      {[1, 2, 3, 4, 5].map(position => (
        <button
          key={position}
          type="button"
          disabled={disabled}
          data-star={position}
          aria-label={language === 'ko' ? `${position}점` : `${position} stars`}
          className="flex-shrink-0 cursor-pointer transition-transform hover:scale-110 disabled:cursor-wait"
          style={{ width: size, height: size }}
          onMouseMove={event => setHover(pick(event, position))}
          onClick={event => {
            event.preventDefault();
            event.stopPropagation();
            const next = pick(event, position);
            setHover(0);
            onChange?.(next);
          }}
        >
          <Star fill={fillFor(shown, position)} />
        </button>
      ))}
    </div>
  );
}
