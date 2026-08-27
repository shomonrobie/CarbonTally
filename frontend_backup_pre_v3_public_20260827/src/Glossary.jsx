// frontend/src/Glossary.jsx
// Public carbon-accounting glossary. Self-contained reference content (see
// public/glossaryData.js) — no backend calls, works offline. Search and
// category filtering run locally.
import React, { useMemo, useState } from 'react';
import PageShell from './public/PageShell';
import { GLOSSARY_TERMS } from './public/glossaryData';

const CATEGORIES = [...new Set(GLOSSARY_TERMS.map((t) => t.category))].sort();

export default function Glossary() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return GLOSSARY_TERMS.filter((t) => {
      const inCategory = category === 'all' || t.category === category;
      if (!inCategory) return false;
      if (!q) return true;
      return (
        t.term.toLowerCase().includes(q) ||
        t.definition.toLowerCase().includes(q)
      );
    }).sort((a, b) => a.term.localeCompare(b.term));
  }, [search, category]);

  return (
    <PageShell
      title="Glossary — CarbonTally"
      description="Plain-English definitions of carbon-accounting and emissions terms: scopes, emission factors, CO2e, GHG Protocol, SECR, CSRD, net zero and more."
    >
      <section className="ct-page-hero">
        <div className="ct-container">
          <h1>Carbon Accounting Glossary</h1>
          <p>
            Plain-English definitions of the terms used across carbon accounting, emissions
            reporting and sustainability compliance — from scopes and emission factors to
            SECR, CSRD and net zero.
          </p>
        </div>
      </section>

      <section className="ct-section">
        <div className="ct-container">
          <div className="ct-glossary-controls" role="search">
            <label className="ct-visually-hidden" htmlFor="glossary-search">Search glossary</label>
            <input
              id="glossary-search"
              type="search"
              className="ct-input"
              placeholder="Search terms…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <label className="ct-visually-hidden" htmlFor="glossary-filter">Filter by category</label>
            <select
              id="glossary-filter"
              className="ct-input ct-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="all">All categories</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <p className="ct-glossary-count" role="status">
            {filtered.length} {filtered.length === 1 ? 'term' : 'terms'}
          </p>

          {filtered.length === 0 ? (
            <p className="ct-glossary-empty">No terms match your search.</p>
          ) : (
            <div className="ct-glossary-list">
              {filtered.map((t) => (
                <article className="ct-glossary-item" key={t.term}>
                  <div className="ct-glossary-term">
                    <h2>{t.term}</h2>
                    <span className="ct-badge">{t.category}</span>
                  </div>
                  <p className="ct-glossary-definition">{t.definition}</p>
                  {t.example && (
                    <p className="ct-glossary-example"><strong>Example:</strong> {t.example}</p>
                  )}
                  {t.related && t.related.length > 0 && (
                    <p className="ct-glossary-related"><strong>Related:</strong> {t.related.join(', ')}</p>
                  )}
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </PageShell>
  );
}