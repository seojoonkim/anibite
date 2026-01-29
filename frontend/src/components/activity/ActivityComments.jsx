/**
 * ActivityComments - Comments section for ActivityCard
 */
import { Link } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { getCurrentLevelInfo } from '../../utils/otakuLevels';
import DefaultAvatar from '../common/DefaultAvatar';

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
  onDeleteComment,
  getAvatarUrl,
  currentUser
}) {
  const { language } = useLanguage();

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  if (loading) {
    return (
      <div className="mt-4 border-t pt-4">
        <p className="text-[15px] text-gray-500">{language === 'ko' ? '댓글 로딩 중...' : language === 'ja' ? 'コメント読込中...' : 'Loading comments...'}</p>
      </div>
    );
  }

  return (
    <div className="mt-3 border-t pt-3">
      {/* New Comment Input */}
      {currentUser && (
        <div className="mb-2">
          <div className="flex gap-2 items-start">
            {currentUser.avatar_url ? (
              <img
                src={getAvatarUrl(currentUser.avatar_url)}
                alt={currentUser.display_name || currentUser.username}
                className="w-7 h-7 rounded-full object-cover flex-shrink-0 border border-border"
              />
            ) : (
              <DefaultAvatar
                username={currentUser.username}
                displayName={currentUser.display_name}
                size="xs"
                className="w-7 h-7 flex-shrink-0"
              />
            )}
            <div className="flex-1 flex gap-2">
              <input
                type="text"
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey && newCommentText.trim()) {
                    e.preventDefault();
                    onCommentSubmit();
                  }
                }}
                placeholder={language === 'ko' ? '댓글을 입력하세요...' : language === 'ja' ? 'コメントを入力してください...' : 'Write a comment...'}
                className="flex-1 px-3 py-1.5 text-[14px] border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button
                onClick={onCommentSubmit}
                disabled={!newCommentText.trim()}
                className="px-3 py-1.5 text-[14px] font-semibold text-white rounded-lg transition-colors disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
                style={newCommentText.trim() ? { backgroundColor: '#4EEAF7' } : {}}
              >
                {language === 'ko' ? '작성' : language === 'ja' ? '作成' : 'Post'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comments List */}
      {comments.length > 0 && (
        <div className="space-y-3">
          {comments.map((comment) => {
            const levelInfo = getCurrentLevelInfo(comment.otaku_score || 0, language);

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
                      <DefaultAvatar
                        username={comment.username}
                        displayName={comment.display_name}
                        size="xs"
                        className="w-6 h-6"
                      />
                    )}
                  </Link>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <Link
                        to={`/user/${comment.user_id}`}
                        className="text-[13px] font-medium text-gray-700 hover:text-[#4EEAF7]"
                      >
                        {comment.display_name || comment.username}
                      </Link>
                      <span
                        className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
                        style={{ backgroundColor: levelInfo.bgColor, border: `1px solid ${levelInfo.borderColorHex}` }}
                      >
                        <span style={{ color: levelInfo.color }} className="font-bold">
                          {levelInfo.icon}
                        </span>{' '}
                        <span style={{ color: levelInfo.color }}>{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                      </span>
                      <span className="text-[11px] text-gray-400">
                        {new Date(comment.created_at).toLocaleDateString(language === 'ko' ? 'ko-KR' : language === 'ja' ? 'ja-JP' : 'en-US')}
                      </span>
                    </div>

                    <p className="text-[13px] text-gray-700 whitespace-pre-wrap">{comment.content}</p>

                    <div className="flex items-center gap-2 mt-0.5">
                      {currentUser && (
                        <button
                          onClick={() => setReplyingTo(comment.id)}
                          className="text-[11px] text-gray-500 hover:text-[#4EEAF7]"
                        >
                          {language === 'ko' ? '답글' : language === 'ja' ? '返信' : 'Reply'}
                        </button>
                      )}
                      {currentUser && currentUser.id === comment.user_id && (
                        <button
                          onClick={() => {
                            if (window.confirm(language === 'ko' ? '댓글을 삭제하시겠습니까?' : language === 'ja' ? 'コメントを削除しますか？' : 'Delete this comment?')) {
                              onDeleteComment(comment.id);
                            }
                          }}
                          className="text-[11px] text-red-500 hover:text-red-700"
                        >
                          {language === 'ko' ? '삭제' : language === 'ja' ? '削除' : 'Delete'}
                        </button>
                      )}
                    </div>

                    {/* Reply Input */}
                    {replyingTo === comment.id && (
                      <div className="mt-1.5 flex gap-2">
                        <input
                          type="text"
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey && replyText.trim()) {
                              e.preventDefault();
                              onReplySubmit(comment.id);
                            }
                          }}
                          placeholder={language === 'ko' ? '답글을 입력하세요...' : language === 'ja' ? '返信を入力してください...' : 'Write a reply...'}
                          className="flex-1 px-2 py-1 text-[12px] border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                        <button
                          onClick={() => onReplySubmit(comment.id)}
                          disabled={!replyText.trim()}
                          className="px-2 py-1 text-[12px] font-semibold text-white rounded transition-colors disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
                          style={replyText.trim() ? { backgroundColor: '#4EEAF7' } : {}}
                        >
                          {language === 'ko' ? '작성' : language === 'ja' ? '作成' : 'Post'}
                        </button>
                        <button
                          onClick={() => {
                            setReplyingTo(null);
                            setReplyText('');
                          }}
                          className="px-2 py-1 text-[12px] font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
                        >
                          {language === 'ko' ? '취소' : language === 'ja' ? 'キャンセル' : 'Cancel'}
                        </button>
                      </div>
                    )}

                    {/* Replies */}
                    {comment.replies && comment.replies.length > 0 && (
                      <div className="mt-3 ml-4 space-y-3 border-l-2 border-gray-200 pl-3">
                        {comment.replies.map((reply) => {
                          const replyLevelInfo = getCurrentLevelInfo(reply.otaku_score || 0, language);

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
                                  <DefaultAvatar
                                    username={reply.username}
                                    displayName={reply.display_name}
                                    size="xs"
                                    className="w-5 h-5"
                                  />
                                )}
                              </Link>

                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <Link
                                    to={`/user/${reply.user_id}`}
                                    className="text-[13px] font-medium text-gray-700 hover:text-[#4EEAF7]"
                                  >
                                    {reply.display_name || reply.username}
                                  </Link>
                                  <span
                                    className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
                                    style={{ backgroundColor: replyLevelInfo.bgColor, border: `1px solid ${replyLevelInfo.borderColorHex}` }}
                                  >
                                    <span style={{ color: replyLevelInfo.color }} className="font-bold">
                                      {replyLevelInfo.icon}
                                    </span>{' '}
                                    <span style={{ color: replyLevelInfo.color }}>{replyLevelInfo.level} - {toRoman(replyLevelInfo.rank)}</span>
                                  </span>
                                  <span className="text-[11px] text-gray-400">
                                    {new Date(reply.created_at).toLocaleDateString(
                                      language === 'ko' ? 'ko-KR' : language === 'ja' ? 'ja-JP' : 'en-US'
                                    )}
                                  </span>
                                </div>

                                <p className="text-[13px] text-gray-700 whitespace-pre-wrap">{reply.content}</p>

                                <div className="flex items-center gap-2 mt-0.5">
                                  {currentUser && (
                                    <button
                                      onClick={() => setReplyingTo(comment.id)}
                                      className="text-[11px] text-gray-500 hover:text-[#4EEAF7]"
                                    >
                                      {language === 'ko' ? '답글' : language === 'ja' ? '返信' : 'Reply'}
                                    </button>
                                  )}
                                  {currentUser && currentUser.id === reply.user_id && (
                                    <button
                                      onClick={() => {
                                        if (window.confirm(language === 'ko' ? '댓글을 삭제하시겠습니까?' : language === 'ja' ? '返信を削除しますか？' : 'Delete this reply?')) {
                                          onDeleteComment(reply.id, comment.id);
                                        }
                                      }}
                                      className="text-[11px] text-red-500 hover:text-red-700"
                                    >
                                      {language === 'ko' ? '삭제' : language === 'ja' ? '削除' : 'Delete'}
                                    </button>
                                  )}
                                </div>
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
