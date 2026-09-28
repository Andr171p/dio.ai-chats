import { fileURLToPath, URL } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv, type Plugin, type ProxyOptions } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [
      react(),
      contentSecurityPolicy([env.VITE_AUTH_API_URL, env.VITE_CHATS_API_URL]),
    ],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      // Node резолвит localhost в ::1, и Vite слушает только IPv6 —
      // браузеры, которые идут на 127.0.0.1, получают отказ в соединении
      host: '127.0.0.1',
      port: 5173,
      proxy: {
        '/auth-api': proxyTo(
          env.AUTH_API_TARGET || 'http://localhost:8001',
          '/auth-api',
        ),
        '/chats-api': proxyTo(
          env.CHATS_API_TARGET || 'http://localhost:8000',
          '/chats-api',
        ),
      },
    },
    preview: { host: '127.0.0.1' },
  };
});

function proxyTo(target: string, prefix: string): ProxyOptions {
  return {
    target,
    changeOrigin: true,
    rewrite: (path) => path.slice(prefix.length),
  };
}

/**
 * CSP для production-сборки. В dev не подключается: HMR Vite использует inline-скрипты.
 * Абсолютные адреса API попадают в connect-src, относительные покрывает 'self'.
 */
function contentSecurityPolicy(apiUrls: (string | undefined)[]): Plugin {
  const apiOrigins = apiUrls
    .filter((url): url is string => Boolean(url && /^https?:\/\//.test(url)))
    .map((url) => new URL(url).origin);

  const policy = [
    "default-src 'self'",
    "script-src 'self'",
    // KaTeX и Mermaid пишут inline-стили в разметку
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data:",
    ['connect-src', "'self'", ...apiOrigins].join(' '),
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');

  return {
    name: 'content-security-policy',
    apply: 'build',
    transformIndexHtml: () => [
      {
        tag: 'meta',
        attrs: { 'http-equiv': 'Content-Security-Policy', content: policy },
        injectTo: 'head-prepend',
      },
    ],
  };
}
