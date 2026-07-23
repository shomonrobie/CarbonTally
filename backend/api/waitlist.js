// backend/api/waitlist.js or similar
app.post('/api/waitlist', async (req, res) => {
  try {
    const { email, source } = req.body;
    
    // Validate email
    if (!email || !email.includes('@')) {
      return res.status(400).json({ error: 'Invalid email' });
    }

    // Save to Supabase
    const { data, error } = await supabase
      .from('waitlist')
      .insert([
        { 
          email: email,
          source: source || 'landing_page',
          created_at: new Date().toISOString()
        }
      ]);

    if (error) {
      // If email already exists
      if (error.code === '23505') {
        return res.status(409).json({ error: 'Email already registered' });
      }
      throw error;
    }

    res.status(200).json({ success: true, message: 'Added to waitlist' });
  } catch (error) {
    console.error('Waitlist error:', error);
    res.status(500).json({ error: 'Failed to add to waitlist' });
  }
});