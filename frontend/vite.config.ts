import react from '@vitejs/plugin-react-swc';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: '0.0.0.0'
    },
    define: {
      __APP_VERSION__: JSON.stringify(env.VITE_APP_VERSION || '0.2.0')
    }
  };
});
