/**
 * DefaultAvatar - Consistent default avatar component
 * Used when user has no profile picture set
 */

// Generate gradient based on username for consistent colors
export const getAvatarGradient = (username) => {
  if (!username) return 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';

  // Hash username to get consistent colors
  let hash = 0;
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash);
  }

  const gradients = [
    'linear-gradient(135deg, #833AB4 0%, #E1306C 40%, #F77737 70%, #FCAF45 100%)', // Instagram
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', // Purple
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', // Pink
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', // Blue
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', // Green
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', // Orange
    'linear-gradient(135deg, #30cfd0 0%, #330867 100%)', // Teal
    'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', // Pastel
  ];

  return gradients[Math.abs(hash) % gradients.length];
};

// Size presets
const sizeClasses = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
  xl: 'w-16 h-16 text-xl',
  '2xl': 'w-20 h-20 text-2xl',
  '3xl': 'w-24 h-24 text-3xl',
};

/**
 * DefaultAvatar component
 * @param {string} username - Username to generate gradient and initial
 * @param {string} displayName - Display name (optional, used for initial if provided)
 * @param {string} size - Size preset: 'xs', 'sm', 'md', 'lg', 'xl', '2xl', '3xl'
 * @param {string} className - Additional classes
 */
export default function DefaultAvatar({
  username,
  displayName,
  size = 'md',
  className = ''
}) {
  const initial = (displayName || username || '?').charAt(0).toUpperCase();
  const gradient = getAvatarGradient(username);
  const sizeClass = sizeClasses[size] || sizeClasses.md;

  return (
    <div
      className={`rounded-full flex items-center justify-center border border-border ${sizeClass} ${className}`}
      style={{ background: gradient }}
    >
      <span className="text-white font-bold">
        {initial}
      </span>
    </div>
  );
}
