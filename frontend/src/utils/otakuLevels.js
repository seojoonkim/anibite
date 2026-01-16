// 오타쿠 레벨 시스템 - Instagram gradient colors
// Icons use Unicode symbols that can be styled with CSS
export const levels = [
  {
    name: '루키',
    nameEn: 'Rookie',
    threshold: 0,
    max: 49,
    icon: '◆', // 다이아몬드
    gradient: 'linear-gradient(135deg, #833AB4 0%, #9D3DAD 100%)',
    color: '#833AB4',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-purple-50 to-purple-100',
    borderColor: 'border-purple-200'
  },
  {
    name: '헌터',
    nameEn: 'Hunter',
    threshold: 50,
    max: 119,
    icon: '▲', // 삼각형
    gradient: 'linear-gradient(135deg, #9D3DAD 0%, #C7348F 100%)',
    color: '#9D3DAD',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-purple-50 to-pink-100',
    borderColor: 'border-purple-200'
  },
  {
    name: '워리어',
    nameEn: 'Warrior',
    threshold: 120,
    max: 219,
    icon: '✦', // 별
    gradient: 'linear-gradient(135deg, #C7348F 0%, #E1306C 100%)',
    color: '#E1306C',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-pink-50 to-pink-100',
    borderColor: 'border-pink-200'
  },
  {
    name: '나이트',
    nameEn: 'Knight',
    threshold: 220,
    max: 349,
    icon: '◈', // 다이아몬드 변형
    gradient: 'linear-gradient(135deg, #E1306C 0%, #E9446F 100%)',
    color: '#E9446F',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-pink-50 to-rose-100',
    borderColor: 'border-pink-200'
  },
  {
    name: '마스터',
    nameEn: 'Master',
    threshold: 350,
    max: 549,
    icon: '★', // 별
    gradient: 'linear-gradient(135deg, #E9446F 0%, #F05F4A 100%)',
    color: '#F05F4A',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-rose-50 to-orange-100',
    borderColor: 'border-rose-200'
  },
  {
    name: '하이마스터',
    nameEn: 'High Master',
    threshold: 550,
    max: 799,
    icon: '✧', // 반짝이는 별
    gradient: 'linear-gradient(135deg, #F05F4A 0%, #F77737 100%)',
    color: '#F77737',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-orange-50 to-orange-100',
    borderColor: 'border-orange-200'
  },
  {
    name: '그랜드마스터',
    nameEn: 'Grand Master',
    threshold: 800,
    max: 1099,
    icon: '♔', // 왕관
    gradient: 'linear-gradient(135deg, #F77737 0%, #FA9041 100%)',
    color: '#F77737',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-orange-50 to-amber-100',
    borderColor: 'border-orange-200'
  },
  {
    name: '오타쿠',
    nameEn: 'Otaku',
    threshold: 1100,
    max: 1449,
    icon: '◉', // 원
    gradient: 'linear-gradient(135deg, #FA9041 0%, #FCA842 100%)',
    color: '#FA9041',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-amber-50 to-yellow-100',
    borderColor: 'border-amber-200'
  },
  {
    name: '오타쿠 킹',
    nameEn: 'Otaku King',
    threshold: 1450,
    max: 1799,
    icon: '♕', // 왕관 (채워진)
    gradient: 'linear-gradient(135deg, #FCA842 0%, #FCAF45 100%)',
    color: '#FCAF45',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-yellow-50 to-yellow-100',
    borderColor: 'border-yellow-200'
  },
  {
    name: '오타쿠 갓',
    nameEn: 'Otaku God',
    threshold: 1800,
    max: Infinity,
    icon: '◆', // 다이아몬드 (최고 레벨)
    gradient: 'linear-gradient(135deg, #FCAF45 0%, #FFD700 100%)',
    color: '#FFD700',
    textColor: 'text-white',
    bgGradient: 'bg-gradient-to-br from-yellow-50 to-amber-100',
    borderColor: 'border-yellow-300'
  },
];

export const getCurrentLevelInfo = (score) => {
  for (let i = 0; i < levels.length; i++) {
    if (score <= levels[i].max) {
      return {
        level: levels[i].name,
        icon: levels[i].icon,
        color: levels[i].color,
        gradient: levels[i].gradient,
        textColor: levels[i].textColor,
        bgGradient: levels[i].bgGradient,
        borderColor: levels[i].borderColor,
        rank: i + 1,
        total: levels.length,
        nextLevel: i < levels.length - 1 ? levels[i + 1].name : null,
        nextIcon: i < levels.length - 1 ? levels[i + 1].icon : null,
        nextThreshold: i < levels.length - 1 ? levels[i + 1].threshold : null,
        currentThreshold: levels[i].threshold,
        maxThreshold: levels[i].max
      };
    }
  }
  return {
    level: levels[levels.length - 1].name,
    icon: levels[levels.length - 1].icon,
    color: levels[levels.length - 1].color,
    gradient: levels[levels.length - 1].gradient,
    textColor: levels[levels.length - 1].textColor,
    bgGradient: levels[levels.length - 1].bgGradient,
    borderColor: levels[levels.length - 1].borderColor,
    rank: levels.length,
    total: levels.length,
    nextLevel: null,
    nextIcon: null,
    nextThreshold: null,
    currentThreshold: levels[levels.length - 1].threshold,
    maxThreshold: levels[levels.length - 1].max
  };
};
