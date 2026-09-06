import { useState, useRef } from 'react';
import StarRating from './StarRating';
import { useLanguage } from '../../context/LanguageContext';
export default function RatingEditor({ rating = 0, onSave, disabled = false }) {
 const {language}=useLanguage(); const ko=language==='ko';
 const [draft,setDraft]=useState(null); const [state,setState]=useState('idle'); const inFlight=useRef(false);
 const value=draft ?? rating;
 const save=async next=>{
  if(inFlight.current || disabled)return;
  setDraft(next);setState('pending');inFlight.current=true;
  try{await onSave(next);setDraft(null);setState('success');}catch{setState('error');}finally{inFlight.current=false;}
 };
 return <div className="rating-editor" aria-busy={state==='pending'}>
  <fieldset disabled={disabled || state==='pending'}><legend className="sr-only">{ko?'내 평점':'My rating'}</legend><StarRating rating={value} onRatingChange={save} language={language}/></fieldset>
  <p role="status" aria-live="polite">{state==='pending'?(ko?'저장 중…':'Saving…'):state==='success'?(ko?'저장됨':'Saved'):''}</p>
  {state==='error'&&<div role="alert"><p>{ko?'저장하지 못했습니다. 선택한 값은 유지됩니다.':'Not saved. Your selected value is preserved.'}</p><button type="button" onClick={()=>save(value)}>{ko?'다시 저장':'Retry save'}</button></div>}
 </div>;
}
