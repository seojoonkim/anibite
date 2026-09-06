import { useState } from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import NotificationDropdown from './NotificationDropdown';

export default function Navbar() {
 const {user,logout} = useAuth(); const {language,setLanguage} = useLanguage();
 const navigate = useNavigate(); const location = useLocation(); const [query,setQuery] = useState('');
 const [notifications,setNotifications] = useState(false);
 const labels = language === 'ja' ? ['発見','評価','フィード','ライブラリ'] : language === 'en' ? ['Discover','Rate','Feed','Library'] : ['발견','평가','피드','내 서재'];
 const paths = ['/browse','/rate','/feed','/my-anipass'];
 const links = paths.map((path,i) => <NavLink key={path} to={path} className={({isActive}) => `nav-destination ${isActive || (path === '/rate' && location.pathname === '/rate-characters') ? 'is-active' : ''}`}>{labels[i]}</NavLink>);
 return <>
  <header className="app-header"><div className="app-header-inner">
   <Link to="/browse" className="app-brand"><img src="/logo.svg" width="28" height="28" alt=""/>AniBite</Link>
   <form role="search" className="desktop-search" onSubmit={event=>{event.preventDefault();navigate(`/browse?q=${encodeURIComponent(query.trim())}`);}}><input type="search" aria-label={language==='ko'?'작품 검색':'Search anime'} placeholder={language==='ko'?'작품 검색':'Search anime'} value={query} onChange={event=>setQuery(event.target.value)}/></form>
   <nav className="desktop-navigation" aria-label={language==='ko'?'주요 메뉴':'Main navigation'}>{links}</nav>
   <div className="app-account">
    <select aria-label="Language / 언어" value={language} onChange={event=>setLanguage(event.target.value)}><option value="ko">한국어</option><option value="en">English</option><option value="ja">日本語</option></select>
    {user ? <>
     <div className="relative"><button type="button" aria-label={language==='ko'?'알림':'Notifications'} aria-expanded={notifications} onClick={()=>setNotifications(!notifications)}>♧</button>{notifications && <NotificationDropdown isOpen onClose={()=>setNotifications(false)}/>}</div>
     <details className="account-menu"><summary>{user.display_name || user.username}</summary><div><Link to="/my-anipass">{labels[3]}</Link><Link to="/settings">{language==='ko'?'설정':'Settings'}</Link><Link to="/leaderboard">{language==='ko'?'리더보드':'Leaderboard'}</Link><button type="button" onClick={()=>{logout();navigate('/browse');}}>{language==='ko'?'로그아웃':'Log out'}</button></div></details>
    </> : <Link className="nav-destination" to="/login" state={{from:location.pathname+location.search+location.hash}}>{language==='ko'?'로그인':'Log in'}</Link>}
   </div>
  </div></header>
  <nav className="mobile-navigation" aria-label={language==='ko'?'모바일 주요 메뉴':'Mobile main navigation'}>{links}</nav>
 </>;
}
