import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/status':             'http://localhost:8000',
      '/chat':               'http://localhost:8000',
      '/corpus-info':        'http://localhost:8000',
      '/ingest':             'http://localhost:8000',
      '/upload-pdf':         'http://localhost:8000',
      '/reset-conversation': 'http://localhost:8000',
      '/reset-corpus':       'http://localhost:8000',
      '/evaluate':           'http://localhost:8000',
    },
  },
})

