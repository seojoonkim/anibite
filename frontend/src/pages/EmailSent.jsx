import { useNavigate, useLocation } from 'react-router-dom';

export default function EmailSent() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';
  const username = location.state?.username || '';

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center">
          {/* Email Icon */}
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            이메일을 확인해주세요!
          </h1>

          <p className="text-gray-600 mb-4">
            <span className="font-semibold">{username}</span>님 환영합니다!
          </p>

          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-700 mb-2">
              <span className="font-medium">{email}</span> 으로<br />
              인증 이메일을 보내드렸습니다.
            </p>
            <p className="text-xs text-gray-600">
              이메일의 인증 링크를 클릭하여 회원가입을 완료해주세요.
            </p>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="text-left">
                <p className="text-sm font-medium text-yellow-800">
                  주의사항
                </p>
                <ul className="text-xs text-yellow-700 mt-1 space-y-1">
                  <li>• 인증 링크는 24시간 동안 유효합니다</li>
                  <li>• 스팸 메일함도 확인해주세요</li>
                  <li>• 이메일이 오지 않았다면 재전송할 수 있습니다</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={() => navigate('/login')}
              className="w-full py-2.5 px-4 rounded-lg font-medium transition-colors"
              style={{ backgroundColor: '#3498DB', color: 'white' }}
              onMouseEnter={(e) => (e.target.style.backgroundColor = '#2DD4E4')}
              onMouseLeave={(e) => (e.target.style.backgroundColor = '#3498DB')}
            >
              로그인 페이지로
            </button>

            <button
              onClick={() => navigate('/resend-verification', { state: { email } })}
              className="w-full py-2.5 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
            >
              인증 이메일 재전송
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
