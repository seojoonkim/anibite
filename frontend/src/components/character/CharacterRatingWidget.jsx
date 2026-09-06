import RatingEditor from '../common/RatingEditor';
import { useLanguage } from '../../context/LanguageContext';
export default function CharacterRatingWidget({currentRating,onRate}) {
 const {language}=useLanguage();
 return <section id="my-rating" className="bg-surface rounded-xl border border-border p-5"><h2 className="text-lg font-bold mb-4">{language==='ko'?'내 평가':'My rating'}</h2><RatingEditor rating={currentRating?.rating || 0} onSave={onRate}/></section>;
}
