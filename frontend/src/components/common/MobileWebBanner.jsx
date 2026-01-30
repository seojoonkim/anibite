import { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';

export default function MobileWebBanner() {
  const { language } = useLanguage();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if banner was dismissed
    const dismissed = localStorage.getItem('mobileWebBannerDismissed');

    // Show banner only on mobile screens and if not dismissed
    const isMobile = window.innerWidth < 768;
    if (isMobile && !dismissed) {
      setIsVisible(true);
    }
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem('mobileWebBannerDismissed', 'true');
  };

  if (!isVisible) return null;

  const messages = {
    ko: '현재 웹 버전으로 사용 가능합니다',
    ja: '現在ウェブ版でご利用いただけます',
    en: 'Currently available as web version'
  };

  return (
    <div className="fixed top-10 md:top-12 left-0 right-0 bg-gradient-to-r from-[#47B5FF] to-[#2DA0ED] text-white z-40 md:hidden">
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2 flex-1">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-medium">
            {messages[language] || messages.en}
          </p>
        </div>
        <button
          onClick={handleDismiss}
          className="ml-2 p-1 hover:bg-white/20 rounded transition-colors flex-shrink-0"
          aria-label="Close banner"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
