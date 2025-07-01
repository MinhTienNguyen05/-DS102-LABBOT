import { defineConfig } from 'vite';
import { resolve } from 'path';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
    root: '.',
    base: 'static/',
    build: {
        manifest: 'manifest.json',
        outDir: './vite_assets',
        rollupOptions: {
            input: {
                main: 'static/global/js/main.js',
            },
        },
        emptyOutDir: true,
    },
    plugins: [tailwindcss()],
});
