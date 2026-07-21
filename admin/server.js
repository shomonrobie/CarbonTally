// server.js - Updated
const express = require('express');
const path = require('path');
const app = express();

const PORT = process.env.PORT || 3001;

// Serve static files from build folder for both /admin and root
app.use('/admin', express.static(path.join(__dirname, 'build')));
app.use(express.static(path.join(__dirname, 'build')));

// Handle all routes for /admin
app.get('/admin/*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Handle root routes
app.get('/*', (req, res) => {
  // Skip if it's a static file
  if (req.path.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|json|html)$/)) {
    return res.sendFile(path.join(__dirname, 'build', req.path));
  }
  // Otherwise serve index.html
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`✅ Admin dashboard running on:`);
  console.log(`   📱 http://localhost:${PORT}`);
  console.log(`   🛠️  http://localhost:${PORT}/admin`);
});