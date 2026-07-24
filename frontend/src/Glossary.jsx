// frontend/src/pages/Glossary.jsx
import React, { useState, useEffect } from 'react';
import './css/Glossary.css';

import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';

const API_URL = process.env.REACT_APP_API_URL || 'https://carbontally-api.onrender.com';

export default function Glossary() {
  const [terms, setTerms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchGlossary();
  }, []);

  const fetchGlossary = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/glossary`);
      const data = await response.json();
      if (data.success) {
        setTerms(data.data);
        // Extract unique categories
        const uniqueCategories = [...new Set(data.data.map(t => t.category).filter(Boolean))];
        setCategories(uniqueCategories);
      }
    } catch (error) {
      console.error('Error fetching glossary:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTerms = terms.filter(term => {
    const matchesSearch = term.term.toLowerCase().includes(search.toLowerCase()) ||
                          term.definition.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || term.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="policy-page-wrapper">
        <AppHeader />  
    <div className="glossary-page">
      
      <div className="glossary-header">
        <h1>Carbon Accounting Glossary</h1>
        <p>Understand key terms and concepts in carbon accounting, emissions reporting, and sustainability compliance.</p>
      </div>

      {/* Search and Filter */}
      <div className="glossary-controls">
        <input
          type="text"
          placeholder="Search terms..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="glossary-search"
        />
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="glossary-filter"
        >
          <option value="all">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Terms List */}
      {loading ? (
        <div className="glossary-loading">Loading glossary...</div>
      ) : (
        <div className="glossary-list">
          {filteredTerms.length === 0 ? (
            <div className="glossary-empty">No terms found matching your criteria.</div>
          ) : (
            filteredTerms.map((term) => (
              <div key={term.id} className="glossary-item">
                <div className="glossary-term">
                  <h3>{term.term}</h3>
                  {term.category && (
                    <span className="glossary-category">{term.category}</span>
                  )}
                </div>
                <p className="glossary-definition">{term.definition}</p>
                {term.example && (
                  <div className="glossary-example">
                    <strong>Example:</strong> {term.example}
                  </div>
                )}
                {term.related_terms && term.related_terms.length > 0 && (
                  <div className="glossary-related">
                    <strong>Related:</strong> {term.related_terms.join(', ')}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
      
    </div>
    <AppFooter />  
    </div>
    
  );
}