/**
 * ActivityComments - Comments section for ActivityCard
 */
import { Link } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { getCurrentLevelInfo } from '../../utils/otakuLevels';

export default function ActivityComments({
  comments,
  loading,
  newCommentText,
  setNewCommentText,
  replyingTo,
  setReplyingTo,
  replyText,
  setReplyText,
  onCommentSubmit,
  onReplySubmit,
  getAvatarUrl
}) {
  const { language } = useLanguage();
  const { user } = useAuth();

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  if (loading) {
    return (
      <div className="mt-4 border-t pt-4">
        <p className="text-sm text-gray-500">{language === 'ko' ? '댓글 로딩 중...' : 'Loading comments...'}</p>
      </div>
    );
  }

  return (
    <div className="mt-4 border-t pt-4">
      {/* New Comment Input */}
      {user && (
        <div className="mb-4">
          <div className="flex gap-2">
            {user.avatar_url ? (
              <img
                src={getAvatarUrl(user.avatar_url)}
                alt={user.display_name || user.username}
                className="w-8 h-8 rounded-full object-cover flex-shrink-0"
              />
            ) : (
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}
              >
                <span className="text-white text-xs font-bold">
                  {(user.display_name || user.username || '?').charAt(0).toUpperCase()}
                </span>
              </div>
            )}
            <div className="flex-1">
              <textarea
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                placeholder={language === 'ko' ? '댓글을 입력하세요...' : 'Write a comment...'}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#A8E6CF] resize-none"
                rows="2"
              />
              <div className="mt-2 flex justify-end">
                <button
                  onClick={onCommentSubmit}
                  disabled={!newCommentText.trim()}
                  className="px-4 py-1.5 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{
                    background: newCommentText.trim()
                      ? 'linear-gradient(135deg, #A8E6CF 0%, #8EC5FC 100%)'
                      : '#ccc'
                  }}
                >
                  {language === 'ko' ? '댓글 작성' : 'Comment'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Comments List */}
      {comments.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-4">
          {language === 'ko' ? '첫 댓글을 작성해보세요!' : 'Be the first to comment!'}
        </p>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => {
            const levelInfo = getCurrentLevelInfo(comment.otaku_score || 0);

            return (
              <div key={comment.id}>
                {/* Top-level Comment */}
                <div className="flex gap-2">
                  <Link to={`/user/${comment.user_id}`} className="flex-shrink-0">
                    {comment.avatar_url ? (
                      <img
                        src={getAvatarUrl(comment.avatar_url)}
                        alt={comment.display_name || comment.username}
                        className="w-6 h-6 rounded-full object-cover"
                      />
                    ) : (
                      <div
                        className="w-6 h-6 rounded-full flex items-center justify-center"
                        style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}
                      >
                        <span className="text-white text-xs font-bold">
                          {(comment.display_name || comment.username || '?').charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                  </Link>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Link
                        to={`/user/${comment.user_id}`}
                        className="text-sm font-medium text-gray-700 hover:text-[#A8E6CF]"
                      >
                        {comment.display_name || comment.username}
                      </Link>
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded-full ${levelInfo.bgGradient} border ${levelInfo.borderColor}`}
                      >
                        <span style={{ color: levelInfo.color }} className="font-bold">
                          {levelInfo.icon}
                        </span>
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(comment.created_at).toLocaleDateString(language === 'ko' ? 'ko-KR' : 'en-US')}
                      </span>
                    </div>

                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{comment.content}</p>

                    {user && (
                      <button
                        onClick={() => setReplyingTo(comment.id)}
                        className="mt-1 text-xs text-gray-500 hover:text-[#A8E6CF]"
                      >
                        {language === 'ko' ? '답글' : 'Reply'}
                      </button>
                    )}

                    {/* Reply Input */}
                    {replyingTo === comment.id && (
                      <div className="mt-2 flex gap-2">
                        <textarea
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          placeholder={language === 'ko' ? '답글을 입력하세요...' : 'Write a reply...'}
                          className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#A8E6CF] resize-none"
                          rows="2"
                        />
                        <div className="flex flex-col gap-1">
                          <button
                            onClick={() => onReplySubmit(comment.id)}
                            disabled={!replyText.trim()}
                            className="px-3 py-1 text-xs font-medium text-white rounded transition-colors disabled:opacity-50"
                            style={{
                              background: replyText.trim()
                                ? 'linear-gradient(135deg, #A8E6CF 0%, #8EC5FC 100%)'
                                : '#ccc'
                            }}
                          >
                            {language === 'ko' ? '작성' : 'Reply'}
                          </button>
                          <button
                            onClick={() => {
                              setReplyingTo(null);
                              setReplyText('');
                            }}
                            className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
                          >
                            {language === 'ko' ? '취소' : 'Cancel'}
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Replies */}
                    {comment.replies && comment.replies.length > 0 && (
                      <div className="mt-3 ml-6 space-y-3 border-l-2 border-gray-200 pl-3">
                        {comment.replies.map((reply) => {
                          const replyLevelInfo = getCurrentLevelInfo(reply.otaku_score || 0);

                          return (
                            <div key={reply.id} className="flex gap-2">
                              <Link to={`/user/${reply.user_id}`} className="flex-shrink-0">
                                {reply.avatar_url ? (
                                  <img
                                    src={getAvatarUrl(reply.avatar_url)}
                                    alt={reply.display_name || reply.username}
                                    className="w-5 h-5 rounded-full object-cover"
                                  />
                                ) : (
                                  <div
                                    className="w-5 h-5 rounded-full flex items-center justify-center"
                                    style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}
                                  >
                                    <span className="text-white text-[10px] font-bold">
                                      {(reply.display_name || reply.username || '?').charAt(0).toUpperCase()}
                                    </span>
                                  </div>
                                )}
                              </Link>

                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <Link
                                    to={`/user/${reply.user_id}`}
                                    className="text-xs font-medium text-gray-700 hover:text-[#A8E6CF]"
                                  >
                                    {reply.display_name || reply.username}
                                  </Link>
                                  <span
                                    className={`text-[10px] px-1 py-0.5 rounded-full ${replyLevelInfo.bgGradient} border ${replyLevelInfo.borderColor}`}
                                  >
                                    <span style={{ color: replyLevelInfo.color }} className="font-bold">
                                      {replyLevelInfo.icon}
                                    </span>
                                  </span>
                                  <span className="text-[10px] text-gray-400">
                                    {new Date(reply.created_at).toLocaleDateString(
                                      language === 'ko' ? 'ko-KR' : 'en-US'
                                    )}
                                  </span>
                                </div>

                                <p className="text-xs text-gray-700 whitespace-pre-wrap">{reply.content}</p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
