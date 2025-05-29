#!/usr/bin/env node

/**
 * Netlify Deployment Preparation Script
 * 
 * This script helps prepare the Truck Dispatch Optimization System
 * for deployment on Netlify by checking configuration and providing
 * deployment guidance.
 */

const fs = require('fs');
const path = require('path');

console.log('🚛 Netlify Deployment Preparation for Truck Dispatch System');
console.log('============================================================');

// Check if we're in the correct directory
const currentDir = process.cwd();
const packageJsonPath = path.join(currentDir, 'src', 'front', 'package.json');

if (!fs.existsSync(packageJsonPath)) {
  console.error('❌ Error: Please run this script from the project root directory');
  console.error('   Expected to find: src/front/package.json');
  process.exit(1);
}

console.log('✅ Project structure verified');

// Check if netlify.toml exists
const netlifyConfigPath = path.join(currentDir, 'netlify.toml');
if (fs.existsSync(netlifyConfigPath)) {
  console.log('✅ netlify.toml configuration found');
} else {
  console.log('⚠️  netlify.toml not found - this will be created automatically');
}

// Check environment configuration
const envExamplePath = path.join(currentDir, 'src', 'front', 'env.example');
if (fs.existsSync(envExamplePath)) {
  console.log('✅ Environment configuration example found');
} else {
  console.log('⚠️  Environment configuration example not found');
}

// Check if backend is configured for production
const serverPath = path.join(currentDir, 'src', 'api', 'server.py');
if (fs.existsSync(serverPath)) {
  const serverContent = fs.readFileSync(serverPath, 'utf8');
  if (serverContent.includes('PORT')) {
    console.log('✅ Backend appears to be configured for production deployment');
  } else {
    console.log('⚠️  Backend may need PORT environment variable configuration');
  }
}

console.log('\n📋 Deployment Checklist:');
console.log('========================');

console.log('\n1. Backend Deployment (REQUIRED FIRST):');
console.log('   □ Deploy backend to Railway, Render, or Heroku');
console.log('   □ Get your backend URL (e.g., https://your-app.railway.app)');
console.log('   □ Test backend health endpoint: YOUR_BACKEND_URL/api/status');

console.log('\n2. Frontend Configuration:');
console.log('   □ Set VITE_API_BASE_URL environment variable in Netlify');
console.log('   □ Value should be your deployed backend URL');

console.log('\n3. Netlify Deployment:');
console.log('   □ Connect repository to Netlify');
console.log('   □ Set build directory: src/front');
console.log('   □ Set build command: npm ci --legacy-peer-deps && npm run build');
console.log('   □ Set publish directory: src/front/dist');

console.log('\n4. CORS Configuration:');
console.log('   □ Update backend CORS settings to include your Netlify domain');
console.log('   □ Add "https://your-app.netlify.app" to allowed origins');

console.log('\n🔗 Useful Commands:');
console.log('==================');
console.log('Test local build:     cd src/front && npm run build');
console.log('Preview build:        cd src/front && npm run preview');
console.log('Deploy via CLI:       netlify deploy --prod --dir=src/front/dist');

console.log('\n📚 For detailed instructions, see: deployment-guide.md');

console.log('\n🚀 Ready to deploy!');
console.log('   1. Deploy backend first');
console.log('   2. Update frontend environment variables');
console.log('   3. Deploy frontend to Netlify'); 