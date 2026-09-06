/**
 * DefaultAvatar - Consistent default avatar component
 * Used when user has no profile picture set
 */

// Generate gradient based on username for consistent colors
import { getAvatarGradient } from './avatarGradient';

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
