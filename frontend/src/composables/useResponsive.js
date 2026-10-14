import { onScopeDispose, ref } from 'vue'

/**
 * 把 window.matchMedia 包装成响应式布尔值。
 * 在作用域销毁时自动注销监听，避免路由切换造成泄漏。
 */
export function useMediaQuery(query) {
  const mql = window.matchMedia(query)
  const matches = ref(mql.matches)
  const onChange = (e) => {
    matches.value = e.matches
  }
  mql.addEventListener('change', onChange)
  onScopeDispose(() => mql.removeEventListener('change', onChange))
  return matches
}

/** 手机 / 竖屏小平板（与 Element Plus 的 xs 断点一致） */
export const useIsMobile = () => useMediaQuery('(max-width: 768px)')
