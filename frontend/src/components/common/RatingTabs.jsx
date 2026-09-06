import { NavLink } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
export default function RatingTabs(){const {language}=useLanguage();return <nav className="rating-tabs" aria-label={language==='ko'?'평가 대상':'Rating category'}><NavLink to="/rate">{language==='ko'?'작품':'Anime'}</NavLink><NavLink to="/rate-characters">{language==='ko'?'캐릭터':'Characters'}</NavLink></nav>;}
