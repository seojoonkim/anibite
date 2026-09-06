import { createContext, useContext } from 'react';

export const LogoWiggleContext = createContext();

export function useLogoWiggle() {
  const context = useContext(LogoWiggleContext);
  if (!context) {
    throw new Error('useLogoWiggle must be used within a LogoWiggleProvider');
  }
  return context;
}
