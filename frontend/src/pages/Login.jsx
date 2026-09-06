import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import GoogleSignInButton from '../components/GoogleSignInButton';
import { safeReturnPath } from '../components/common/returnPath';

const copy = {
 ko: {title:'로그인', intro:'좋아하는 작품을 발견하고, 나만의 취향을 기록하세요.', username:'아이디 또는 이메일', password:'비밀번호', show:'비밀번호 표시', hide:'비밀번호 숨기기', submit:'로그인', pending:'로그인 중…', email:'이메일 계정으로 로그인', oauth:'Google로 가입한 계정은 Google 로그인을 이용하세요. 로그인이 차단되면 일반 Chrome 또는 Safari에서 다시 시도해주세요.', signup:'회원가입', browse:'가입 없이 작품 둘러보기', resend:'인증 이메일 다시 보내기', failed:'로그인에 실패했습니다. 다시 시도해주세요.'},
 en: {title:'Log in',intro:'Discover anime. Keep a record of your taste.',username:'Username or email',password:'Password',show:'Show password',hide:'Hide password',submit:'Log in',pending:'Logging in…',email:'Sign in with an email account',oauth:'Accounts created with Google should use Google sign-in. If blocked, try a regular Chrome or Safari browser.',signup:'Sign up',browse:'Explore without an account',resend:'Resend verification email',failed:'Login failed. Please try again.'},
 ja: {title:'ログイン',intro:'好きな作品を見つけて、好みを記録しましょう。',username:'ユーザー名またはメール',password:'パスワード',show:'パスワードを表示',hide:'パスワードを隠す',submit:'ログイン',pending:'ログイン中…',email:'メールアカウントでログイン',oauth:'Googleで登録した場合はGoogleログインをご利用ください。ブロックされた場合は通常のChromeまたはSafariをお試しください。',signup:'新規登録',browse:'登録せず作品を見る',resend:'認証メールを再送',failed:'ログインに失敗しました。もう一度お試しください。'}
};
export default function Login() {
 const [username,setUsername] = useState(''); const [password,setPassword] = useState('');
 const [error,setError] = useState(''); const [loading,setLoading] = useState(false); const [visible,setVisible] = useState(false);
 const {login} = useAuth(); const {language} = useLanguage(); const navigate = useNavigate(); const location = useLocation();
 const text = copy[language] || copy.ko;
 const destination = safeReturnPath(location.state?.from || new URLSearchParams(location.search).get('returnTo'));
 const submit = async event => {
  event.preventDefault(); if (loading) return; setLoading(true); setError('');
  try { const result = await login({username,password}); if (result.success) navigate(destination,{replace:true}); else setError(typeof result.error === 'string' ? result.error : text.failed); }
  catch { setError(text.failed); } finally { setLoading(false); }
 };
 return <main className="auth-page"><section className="auth-card" aria-labelledby="login-title">
  <Link to="/browse" className="auth-brand"><img src="/logo.svg" alt="" width="40" height="40"/>AniBite</Link>
  <p className="text-text-secondary">{text.intro}</p><h1 id="login-title">{text.title}</h1>
  <GoogleSignInButton onError={setError} returnTo={destination}/><p className="auth-help">{text.oauth}</p>
  <p className="auth-divider">{text.email}</p>
  {error && <div role="alert" className="form-error">{error}{/not verified/i.test(error) && <Link to="/resend-verification" state={{email:username.includes('@') ? username : ''}}>{text.resend}</Link>}</div>}
  <form onSubmit={submit} aria-busy={loading}>
   <label htmlFor="login-username">{text.username}</label><input id="login-username" name="username" autoComplete="username" autoCapitalize="none" required value={username} onChange={event=>setUsername(event.target.value)}/>
   <label htmlFor="login-password">{text.password}</label><input id="login-password" name="password" type={visible?'text':'password'} autoComplete="current-password" required value={password} onChange={event=>setPassword(event.target.value)}/>
   <button type="button" className="password-toggle" aria-pressed={visible} onClick={()=>setVisible(!visible)}>{visible?text.hide:text.show}</button>
   <button type="submit" className="button-primary" disabled={loading}>{loading?text.pending:text.submit}</button>
  </form><div className="auth-links"><Link to="/register" state={{from:destination}}>{text.signup}</Link><Link to="/browse">{text.browse}</Link></div>
 </section></main>;
}
