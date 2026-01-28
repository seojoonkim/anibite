// 오타쿠 레벨 시스템 - Instagram gradient colors (Dark mode compatible)
// Icons use Unicode symbols that can be styled with CSS
export const levels = [
  {
    name: '루키',
    nameEn: 'Rookie',
    nameJa: 'ルーキー',
    threshold: 0,
    max: 49,
    icon: '◆', // 다이아몬드
    gradient: 'linear-gradient(135deg, #833AB4 0%, #9D3DAD 100%)',
    color: '#A855F7',
    textColor: 'text-white',
    bgColor: 'rgba(168, 85, 247, 0.15)',
    borderColorHex: 'rgba(168, 85, 247, 0.3)'
  },
  {
    name: '헌터',
    nameEn: 'Hunter',
    nameJa: 'ハンター',
    threshold: 50,
    max: 119,
    icon: '▲', // 삼각형
    gradient: 'linear-gradient(135deg, #9D3DAD 0%, #C7348F 100%)',
    color: '#C026D3',
    textColor: 'text-white',
    bgColor: 'rgba(192, 38, 211, 0.15)',
    borderColorHex: 'rgba(192, 38, 211, 0.3)'
  },
  {
    name: '워리어',
    nameEn: 'Warrior',
    nameJa: 'ウォーリアー',
    threshold: 120,
    max: 219,
    icon: '✦', // 별
    gradient: 'linear-gradient(135deg, #C7348F 0%, #E1306C 100%)',
    color: '#EC4899',
    textColor: 'text-white',
    bgColor: 'rgba(236, 72, 153, 0.15)',
    borderColorHex: 'rgba(236, 72, 153, 0.3)'
  },
  {
    name: '나이트',
    nameEn: 'Knight',
    nameJa: 'ナイト',
    threshold: 220,
    max: 349,
    icon: '◈', // 다이아몬드 변형
    gradient: 'linear-gradient(135deg, #E1306C 0%, #E9446F 100%)',
    color: '#F43F5E',
    textColor: 'text-white',
    bgColor: 'rgba(244, 63, 94, 0.15)',
    borderColorHex: 'rgba(244, 63, 94, 0.3)'
  },
  {
    name: '마스터',
    nameEn: 'Master',
    nameJa: 'マスター',
    threshold: 350,
    max: 549,
    icon: '★', // 별
    gradient: 'linear-gradient(135deg, #E9446F 0%, #F05F4A 100%)',
    color: '#EF4444',
    textColor: 'text-white',
    bgColor: 'rgba(239, 68, 68, 0.15)',
    borderColorHex: 'rgba(239, 68, 68, 0.3)'
  },
  {
    name: '하이마스터',
    nameEn: 'High Master',
    nameJa: 'ハイマスター',
    threshold: 550,
    max: 799,
    icon: '✧', // 반짝이는 별
    gradient: 'linear-gradient(135deg, #F05F4A 0%, #F77737 100%)',
    color: '#F97316',
    textColor: 'text-white',
    bgColor: 'rgba(249, 115, 22, 0.15)',
    borderColorHex: 'rgba(249, 115, 22, 0.3)'
  },
  {
    name: '그랜드마스터',
    nameEn: 'Grand Master',
    nameJa: 'グランドマスター',
    threshold: 800,
    max: 1099,
    icon: '♔', // 왕관
    gradient: 'linear-gradient(135deg, #F77737 0%, #FA9041 100%)',
    color: '#FB923C',
    textColor: 'text-white',
    bgColor: 'rgba(251, 146, 60, 0.15)',
    borderColorHex: 'rgba(251, 146, 60, 0.3)'
  },
  {
    name: '오타쿠',
    nameEn: 'Otaku',
    nameJa: 'オタク',
    threshold: 1100,
    max: 1449,
    icon: '◉', // 원
    gradient: 'linear-gradient(135deg, #FA9041 0%, #FCA842 100%)',
    color: '#FBBF24',
    textColor: 'text-white',
    bgColor: 'rgba(251, 191, 36, 0.15)',
    borderColorHex: 'rgba(251, 191, 36, 0.3)'
  },
  {
    name: '오타쿠 킹',
    nameEn: 'Otaku King',
    nameJa: 'オタクキング',
    threshold: 1450,
    max: 1799,
    icon: '♕', // 왕관 (채워진)
    gradient: 'linear-gradient(135deg, #FCA842 0%, #FCAF45 100%)',
    color: '#FCD34D',
    textColor: 'text-white',
    bgColor: 'rgba(252, 211, 77, 0.15)',
    borderColorHex: 'rgba(252, 211, 77, 0.3)'
  },
  {
    name: '오타쿠 갓',
    nameEn: 'Otaku God',
    nameJa: 'オタクゴッド',
    threshold: 1800,
    max: Infinity,
    icon: '◆', // 다이아몬드 (최고 레벨)
    gradient: 'linear-gradient(135deg, #FCAF45 0%, #FFD700 100%)',
    color: '#FFD700',
    textColor: 'text-white',
    bgColor: 'rgba(255, 215, 0, 0.15)',
    borderColorHex: 'rgba(255, 215, 0, 0.3)'
  },
];

export const getCurrentLevelInfo = (score, language = 'ko') => {
  const getLevelName = (level) => {
    if (language === 'ko') return level.name;
    if (language === 'ja') return level.nameJa;
    return level.nameEn;
  };

  for (let i = 0; i < levels.length; i++) {
    if (score <= levels[i].max) {
      return {
        level: getLevelName(levels[i]),
        levelKo: levels[i].name,
        levelEn: levels[i].nameEn,
        levelJa: levels[i].nameJa,
        icon: levels[i].icon,
        color: levels[i].color,
        gradient: levels[i].gradient,
        textColor: levels[i].textColor,
        bgColor: levels[i].bgColor,
        borderColorHex: levels[i].borderColorHex,
        rank: i + 1,
        total: levels.length,
        nextLevel: i < levels.length - 1 ? getLevelName(levels[i + 1]) : null,
        nextLevelKo: i < levels.length - 1 ? levels[i + 1].name : null,
        nextLevelEn: i < levels.length - 1 ? levels[i + 1].nameEn : null,
        nextLevelJa: i < levels.length - 1 ? levels[i + 1].nameJa : null,
        nextIcon: i < levels.length - 1 ? levels[i + 1].icon : null,
        nextThreshold: i < levels.length - 1 ? levels[i + 1].threshold : null,
        currentThreshold: levels[i].threshold,
        maxThreshold: levels[i].max
      };
    }
  }
  const lastLevel = levels[levels.length - 1];
  return {
    level: getLevelName(lastLevel),
    levelKo: lastLevel.name,
    levelEn: lastLevel.nameEn,
    levelJa: lastLevel.nameJa,
    icon: lastLevel.icon,
    color: lastLevel.color,
    gradient: lastLevel.gradient,
    textColor: lastLevel.textColor,
    bgColor: lastLevel.bgColor,
    borderColorHex: lastLevel.borderColorHex,
    rank: levels.length,
    total: levels.length,
    nextLevel: null,
    nextLevelKo: null,
    nextLevelEn: null,
    nextLevelJa: null,
    nextIcon: null,
    nextThreshold: null,
    currentThreshold: lastLevel.threshold,
    maxThreshold: lastLevel.max
  };
};
