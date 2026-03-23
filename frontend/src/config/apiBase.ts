/**
 * 后端 API 根地址（不含尾部斜杠）。
 * - 优先使用环境变量 VITE_API_BASE_URL（见 .env.example）
 * - 浏览器内未配置时，使用当前页面的 hostname + :8000，便于手机通过局域网 IP 访问
 * - 构建/非浏览器环境回退 localhost
 */
export function getApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (fromEnv != null && String(fromEnv).trim() !== '') {
    return String(fromEnv).replace(/\/$/, '');
  }
  if (typeof window !== 'undefined' && window.location?.hostname) {
    const { hostname, protocol } = window.location;
    const proto = protocol === 'https:' ? 'https:' : 'http:';
    return `${proto}//${hostname}:8000`;
  }
  return 'http://localhost:8000';
}
