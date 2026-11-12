// 좁은 화면(폰)인지 봅니다. index.css 의 모바일 기준(760px)과 같은 값을 씁니다.
// 렌더할 때 한 번 읽는 값이라 창 크기를 바꾸면 다음 렌더부터 반영됩니다(3D 장면 높이처럼 CSS 로 바꿀 수 없는 값에만 씁니다).
export const isMobile = (): boolean => typeof window !== 'undefined' && window.matchMedia('(max-width: 760px)').matches

/** 데스크톱 값과 모바일 값 중 지금 화면에 맞는 쪽을 돌려줍니다. */
export const mh = (desktop: number, mobile: number): number => (isMobile() ? mobile : desktop)
