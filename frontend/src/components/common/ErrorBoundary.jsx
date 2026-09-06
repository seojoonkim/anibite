import { Component } from 'react';
export default class ErrorBoundary extends Component {
 state = {failed:false};
 static getDerivedStateFromError() { return {failed:true}; }
 render() {
  if (this.state.failed) return <section className="recovery-page" role="alert"><h1>화면을 불러오지 못했습니다</h1><p>입력한 내용을 확인한 뒤 다시 시도해주세요.</p><button type="button" className="button-primary" onClick={()=>window.location.reload()}>다시 불러오기</button><a href="/browse">작품 둘러보기</a></section>;
  return this.props.children;
 }
}
