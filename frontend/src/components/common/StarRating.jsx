export default function StarRating({ rating = 0, onRatingChange, readonly = false, size = 'md', showNumber = true, align = 'left', language = 'ko' }) {
  const value = Math.max(0, Math.min(5, Number(rating) || 0));
  const ko = language === 'ko';
  const label = value ? (ko ? `5점 만점에 ${value}점` : `${value} out of 5`) : (ko ? '평가하지 않음' : 'Not rated');
  const stars = <span aria-hidden="true" className="rating-stars"><span>★★★★★</span><span style={{ width: `${value * 20}%` }}>★★★★★</span></span>;
  if (readonly) return <span role="img" aria-label={label} className={`rating-readonly rating-${size}`}>{stars}{showNumber && value > 0 && <span>{value.toFixed(1)}</span>}</span>;
  const change = next => onRatingChange?.(Math.max(0, Math.min(5, next)));
  return <div className={`rating-input rating-${size}`} style={{ textAlign: align }}>
    <div className="rating-adjustments">
      <button type="button" aria-label={ko ? '0.5점 내리기' : 'Decrease by 0.5'} disabled={value === 0} onClick={() => change(value - 0.5)}>−</button>
      <input type="range" min="0" max="5" step="0.5" value={value} aria-label={ko ? '내 평점' : 'My rating'} aria-valuenow={value} aria-valuetext={label}
        onChange={e => change(Number(e.target.value))}
        onKeyDown={e => { const next = { ArrowRight: value + 0.5, ArrowUp: value + 0.5, ArrowLeft: value - 0.5, ArrowDown: value - 0.5, Home: 0, End: 5 }[e.key]; if (next !== undefined) { e.preventDefault(); change(next); } }}/>
      <button type="button" aria-label={ko ? '0.5점 올리기' : 'Increase by 0.5'} disabled={value === 5} onClick={() => change(value + 0.5)}>+</button>
    </div>
    <div className="rating-caption"><span role="status" aria-live="polite">{value ? `★ ${value.toFixed(1)} / 5` : label}</span><button type="button" onClick={() => change(0)} disabled={value === 0}>{ko ? '평가 지우기' : 'Clear rating'}</button></div>
  </div>;
}
