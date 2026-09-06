import { useState, useCallback } from 'react';

import { LogoWiggleContext } from './LogoWiggleContext';

export function LogoWiggleProvider({ children }) {
  const [isWiggling, setIsWiggling] = useState(false);

  const triggerWiggle = useCallback(() => {
    // 이미 흔들리고 있으면 무시
    if (isWiggling) return;

    setIsWiggling(true);

    // 애니메이션 완료 후 상태 리셋 (0.8초 - 더 부드러운 애니메이션)
    setTimeout(() => {
      setIsWiggling(false);
    }, 800);
  }, [isWiggling]);

  return (
    <LogoWiggleContext.Provider value={{ isWiggling, triggerWiggle }}>
      {children}
    </LogoWiggleContext.Provider>
  );
}

