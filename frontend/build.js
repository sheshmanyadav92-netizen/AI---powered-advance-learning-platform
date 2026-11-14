import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const distDir = path.join(__dirname, 'dist');
if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
}

// Read template from backend static or source
const templatePath = path.join(__dirname, '..', 'backend', 'app', 'static', 'index.html');
let content = fs.readFileSync(templatePath, 'utf-8');

fs.writeFileSync(path.join(distDir, 'index.html'), content, 'utf-8');
console.log('✓ Successfully bundled frontend to dist/index.html');

