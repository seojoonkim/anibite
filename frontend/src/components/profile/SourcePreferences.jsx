import { useLanguage } from '../../context/LanguageContext';

export default function SourcePreferences({ sources }) {
  const { language } = useLanguage();

  const maxCount = sources && sources.distribution && sources.distribution.length > 0
    ? Math.max(...sources.distribution.map(s => s.count))
    : 1;

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">
        {language === 'ko' ? '원작 매체 선호도' : 'Source Material Preferences'}
      </h3>

      {!sources || !sources.distribution || sources.distribution.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          {language === 'ko' ? '데이터가 없습니다' : 'No data available'}
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {sources.distribution.map((source) => {
          const percentage = (source.count / maxCount) * 100;

          return (
            <div key={source.source_display}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {source.source_display}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">{source.count}개</span>
                  <span className="text-xs text-yellow-600">★ {source.average_rating?.toFixed(1)}</span>
                </div>
              </div>
              <div className="bg-gray-100 rounded-full h-2">
                <div
                  className="h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${percentage}%`,
                    background: 'linear-gradient(to right, #A8E6CF, #2C7CB8)'
                  }}
                />
              </div>
            </div>
          );
        })}
          </div>

          {/* Top source */}
          {sources.top_source && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-600">
                {language === 'ko' ? '가장 선호하는 원작: ' : 'Most preferred source: '}
                <span className="font-semibold text-gray-900">{sources.top_source}</span>
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
