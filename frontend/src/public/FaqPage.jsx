// Public website FAQ page.
// Native CarbonTally public-site page: hero, live search, category
// navigation, accessible accordions with deep-linkable anchors, related
// questions, and a launch CTA. Styling lives in faq.css using the ct-* design
// tokens from public-site.css.
import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import PageShell from './PageShell';
import { FAQ_CATEGORIES } from './faqData';
import './faq.css';

const ALL_ITEMS = FAQ_CATEGORIES.flatMap((cat) =>
  cat.items.map((item) => ({ ...item, category: cat.slug, categoryTitle: cat.title }))
);

export default function FaqPage() {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(() => new Set());
  const [copied, setCopied] = useState(null);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    const set = new Set();
    ALL_ITEMS.forEach((item) => {
      if (item.q.toLowerCase().includes(q) || item.a.toLowerCase().includes(q)) set.add(item.id);
    });
    return set;
  }, [query]);

  const toggle = (id) => {
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const isOpen = (id) => (matches ? matches.has(id) : open.has(id));

  // Deep linking: open and scroll to #faq-<id> on load and on hash change.
  // A deep link clears any active search so the target item is always visible.
  useEffect(() => {
    const openFromHash = () => {
      const hash = window.location.hash.replace(/^#/, '');
      if (hash.startsWith('faq-')) {
        const id = hash.slice(4);
        setQuery('');
        setOpen((prev) => new Set(prev).add(id));
        setTimeout(() => {
          document.getElementById(`faq-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 60);
      }
    };
    openFromHash();
    window.addEventListener('hashchange', openFromHash);
    return () => window.removeEventListener('hashchange', openFromHash);
  }, []);

  const copyLink = (id) => {
    const url = `${window.location.origin}${window.location.pathname}#faq-${id}`;
    window.history.replaceState(null, '', `#faq-${id}`);
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url).catch(() => {});
    }
    setCopied(id);
    toast('Link copied to clipboard', { icon: '🔗', duration: 2200 });
    window.setTimeout(() => setCopied(null), 2200);
  };

  const scrollToCategory = (slug) => {
    document.getElementById(`faq-cat-${slug}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const visibleCount = matches ? matches.size : ALL_ITEMS.length;

  return (
    <PageShell
      title="Frequently asked questions | CarbonTally"
      description="Answers about how CarbonTally processes source data into traceable, validated emissions results: documents, extraction, mapping, emission factors, calculations, review, approval, evidence, reporting and more."
    >
      {/* Hero */}
      <section className="ct-section ct-faq-hero">
        <div className="ct-container">
          <div className="ct-faq-hero-inner">
            <span className="ct-eyebrow">Help centre</span>
            <h1>Frequently asked questions</h1>
            <p className="ct-lead">
              How CarbonTally turns messy source data into traceable, validated
              emissions results, and how the service works for you.
            </p>

            <div className="ct-faq-search" role="search">
              <label htmlFor="faq-search" className="ct-visually-hidden">
                Search CarbonTally questions
              </label>
              <input
                id="faq-search"
                type="search"
                autoComplete="off"
                placeholder="Search CarbonTally questions"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              {query.trim() && (
                <span className="ct-faq-search-count">
                  {visibleCount} {visibleCount === 1 ? 'answer' : 'answers'}
                </span>
              )}
            </div>

            <nav className="ct-faq-chips" aria-label="FAQ categories">
              {FAQ_CATEGORIES.map((cat) => (
                <button key={cat.slug} type="button" onClick={() => scrollToCategory(cat.slug)}>
                  {cat.title}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="ct-section ct-faq-body">
        <div className="ct-container">
          {FAQ_CATEGORIES.map((cat) => {
            const items = cat.items.filter((item) => !matches || matches.has(item.id));
            if (matches && items.length === 0) return null;
            return (
              <div key={cat.slug} id={`faq-cat-${cat.slug}`} className="ct-faq-category">
                <div className="ct-faq-cat-head">
                  <h2>{cat.title}</h2>
                  {cat.intro && <p>{cat.intro}</p>}
                </div>
                <div className="ct-faq-list">
                  {items.map((item) => (
                    <FaqItem
                      key={item.id}
                      item={item}
                      isOpen={isOpen(item.id)}
                      copied={copied === item.id}
                      onToggle={() => toggle(item.id)}
                      onCopy={() => copyLink(item.id)}
                      relatedLookup={ALL_ITEMS}
                      onRelated={(id) => {
                        setOpen((prev) => new Set(prev).add(id));
                        document.getElementById(`faq-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                      }}
                    />
                  ))}
                </div>
              </div>
            );
          })}

          {matches && visibleCount === 0 && (
            <div className="ct-faq-empty">
              <h2>No answers match "{query}"</h2>
              <p>Try a different search, or contact CarbonTally with your question.</p>
              <Link to="/contact" className="ct-btn ct-btn-primary">Contact CarbonTally</Link>
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="ct-section-cta">
        <div className="ct-container">
          <h2>Ready to process your emissions data?</h2>
          <p>CarbonTally is preparing for commercial launch — talk to the team about the platform and the processing service.</p>
          <Link to="/contact" className="ct-btn ct-btn-light">Request launch information</Link>
        </div>
      </section>
    </PageShell>
  );
}

function FaqItem({ item, isOpen, copied, onToggle, onCopy, relatedLookup, onRelated }) {
  return (
    <div className={`ct-faq-item${isOpen ? ' ct-open' : ''}`}>
      <h3 className="ct-faq-q">
        <button
          type="button"
          className="ct-faq-q-btn"
          aria-expanded={isOpen}
          aria-controls={`faq-${item.id}`}
          onClick={onToggle}
        >
          <span className="ct-faq-q-icon" aria-hidden="true" />
          <span className="ct-faq-q-text">{item.q}</span>
        </button>
        <button
          type="button"
          className="ct-faq-link-btn"
          aria-label={`Copy link to question: ${item.q}`}
          title="Copy link to this question"
          onClick={onCopy}
        >
          {copied ? 'Copied' : 'Link'}
        </button>
      </h3>
      <div id={`faq-${item.id}`} className="ct-faq-a" hidden={!isOpen}>
        <p>{item.a}</p>
        {item.related && item.related.length > 0 && (
          <p className="ct-faq-related">
            <span>See also:</span>
            {item.related.map((rid, i) => {
              const rel = relatedLookup.find((r) => r.id === rid);
              if (!rel) return null;
              return (
                <React.Fragment key={rid}>
                  {i > 0 && ', '}
                  <button type="button" onClick={() => onRelated(rid)}>{rel.q}</button>
                </React.Fragment>
              );
            })}
          </p>
        )}
      </div>
    </div>
  );
}
