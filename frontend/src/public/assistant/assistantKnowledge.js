// assistantKnowledge.js — Public CarbonTally Assistant knowledge layer.
//
// The website candidate intentionally has NO AI provider configured and NO
// API key in frontend code. This module is a deterministic, local
// knowledge-retrieval layer that answers public questions using the approved
// target-state FAQ content (../faqData.js) as its only knowledge source.
//
// The public assistant:
//   - only knows public-safe content (the customer FAQ)
//   - never claims capabilities the product does not have
//   - answers from the FAQ verbatim, with source attribution
//   - deflects account/data-specific questions (it has no access to them)
//   - says "I don't have enough information" when it does not know
//
// The architecture document (docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md)
// describes how a model provider slots in behind the same handleQuery()
// interface for the production assistant.

import { FAQ_CATEGORIES } from '../faqData';

const ALL_ITEMS = FAQ_CATEGORIES.flatMap((cat) =>
  cat.items.map((item) => ({ ...item, category: cat.slug, categoryTitle: cat.title }))
);

const SOURCE_FAQ = 'CarbonTally Customer FAQ';
const SOURCE_ASSISTANT = 'CarbonTally Assistant';

// ---------------------------------------------------------------------------
// Text helpers
// ---------------------------------------------------------------------------

function normalize(text) {
  return String(text)
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function stem(word) {
  if (word.length <= 4) return word;
  if (word.endsWith('ing')) return word.slice(0, -3);
  if (word.endsWith('ed')) return word.slice(0, -2);
  if (word.endsWith('es')) return word.slice(0, -2);
  if (word.endsWith('s')) return word.slice(0, -1);
  return word;
}

const STOPWORDS = new Set([
  'the', 'a', 'an', 'and', 'or', 'of', 'to', 'in', 'on', 'for', 'with',
  'can', 'does', 'do', 'how', 'is', 'are', 'it', 'that', 'this', 'these',
  'those', 'i', 'you', 'your', 'my', 'me', 'we', 'our', 'us', 'they', 'them',
  'their', 'from', 'by', 'at', 'about', 'please', 'tell', 'know', 'want',
  'what', 'which', 'why', 'who', 'when', 'where', 'all', 'any', 'some', 'will',
  'would', 'should', 'could', 'has', 'have', 'had', 'be', 'been', 'being',
]);

function analyzeQuery(raw) {
  const norm = normalize(raw);
  const rawTokens = norm.split(' ').filter(Boolean);
  const tokens = rawTokens.filter((t) => !STOPWORDS.has(t));
  const stems = tokens.map(stem).filter((s) => s.length >= 4);
  return { norm, rawTokens, tokens, stems };
}

// ---------------------------------------------------------------------------
// Vocabulary aliases: map the user's words to canonical product vocabulary.
// { term: canonical text that appears in FAQ items, tokens: user aliases }
// ---------------------------------------------------------------------------

const VOCAB = [
  { term: 'document', tokens: ['document', 'documents', 'pdf', 'invoice', 'invoices', 'file', 'files', 'upload', 'uploads', 'uploading'] },
  { term: 'scanned', tokens: ['scan', 'scans', 'scanned', 'scanning'] },
  { term: 'spreadsheet', tokens: ['spreadsheet', 'spreadsheets', 'excel', 'csv', 'sheet'] },
  { term: 'extraction', tokens: ['extract', 'extraction', 'extracted', 'extracting'] },
  { term: 'ocr', tokens: ['ocr', 'recogni'] },
  { term: 'mapping', tokens: ['map', 'mapping', 'mapped', 'mappings'] },
  { term: 'emission factor', tokens: ['factor', 'factors', 'emission', 'emissions', 'defra', 'seai', 'irish', 'ireland', 'uk'] },
  { term: 'custom', tokens: ['custom', 'own', 'organisation-specific'] },
  { term: 'calculation', tokens: ['calculate', 'calculation', 'calculated', 'calculations', 'result', 'results'] },
  { term: 'validation', tokens: ['valid', 'validation', 'validate'] },
  { term: 'review', tokens: ['review', 'reviews', 'reviewed'] },
  { term: 'quality control', tokens: ['qc', 'quality', 'control'] },
  { term: 'approval', tokens: ['approve', 'approval', 'approved', 'approving'] },
  { term: 'reject', tokens: ['reject', 'rejected', 'rejection'] },
  { term: 'evidence', tokens: ['evidence', 'proof'] },
  { term: 'trace', tokens: ['trace', 'traceability', 'traced', 'tracing', 'history', 'provenance', 'chain'] },
  { term: 'report', tokens: ['report', 'reports', 'export', 'exports', 'exported'] },
  { term: 'consultant', tokens: ['consultant', 'consultants', 'advisor', 'advisers', 'consultancy', 'consulting', 'agency'] },
  { term: 'processing entity', tokens: ['entity', 'entities', 'partner', 'partners', 'external', 'third-party'] },
  { term: 'assisted', tokens: ['assisted', 'assistance', 'human', 'managed', 'service', 'services', 'team', 'people', 'manual'] },
  { term: 'security', tokens: ['security', 'secure', 'privacy', 'private', 'confidential', 'protected', 'data'] },
  { term: 'pricing', tokens: ['price', 'pricing', 'cost', 'costs', 'charge', 'charged', 'plan', 'billing', 'credit', 'credits'] },
  { term: 'started', tokens: ['started', 'start', 'onboard', 'onboarding', 'begin', 'get-started'] },
  { term: 'auditor', tokens: ['auditor', 'audit', 'verifier', 'verification', 'certification', 'certified', 'certifications', 'iso', 'gdpr', 'regulatory', 'compliance', 'guarantee', 'guarantees'] },
  { term: 'clarification', tokens: ['clarify', 'clarification', 'clarifications'] },
  { term: 'download', tokens: ['download', 'downloaded', 'downloads'] },
  { term: 'organisation', tokens: ['organisation', 'organisations', 'organization', 'workspace', 'company', 'business', 'client'] },
];

// ---------------------------------------------------------------------------
// Scoring
//
// The dominant signal is how much of the user's question overlaps the FAQ
// item's QUESTION (prefix-aware, so "factors" matches "factor"). Answer-text
// overlap is a weaker signal. Vocabulary aliases expand the query with
// canonical product words (e.g. "DEFRA" → emission factor), and an exact
// phrase match dominates everything.
// ---------------------------------------------------------------------------

function wordList(text) {
  return normalize(text)
    .split(' ')
    .filter((w) => w.length >= 3 && !STOPWORDS.has(w));
}

function prefixMatch(word, candidate) {
  // "factors" ~ "factor" ~ "factorisation"
  return word.length >= 4 && (candidate.startsWith(word) || word.startsWith(candidate));
}

function countOverlap(words, candidates) {
  let n = 0;
  for (const w of words) {
    if (candidates.some((c) => prefixMatch(w, c))) n += 1;
  }
  return n;
}

// Expand the query with canonical vocabulary words triggered by aliases.
function expandQueryWords(q) {
  const words = new Set([...q.tokens, ...q.stems].filter((w) => w.length >= 2));
  for (const v of VOCAB) {
    if (v.tokens.some((t) => q.tokens.includes(t) || q.stems.includes(t))) {
      v.term.split(' ').forEach((w) => words.add(w));
    }
  }
  return [...words];
}

// Disambiguation hints for compound public terms where plain word overlap is
// ambiguous. These are curated public-vocabulary mappings, not product claims.
const PHRASE_HINTS = [
  { phrases: ['emissions mapping', 'emission mapping', 'activity mapping', 'mapping emissions'], ids: ['what-does-mapping-mean'], boost: 45 },
  { phrases: ['processing entities', 'external processing', 'external teams'], ids: ['what-are-processing-entities'], boost: 30 },
  { phrases: ['custom emission factors', 'own emission factors', 'custom factors'], ids: ['custom-factors'], boost: 30 },
  { phrases: ['defra factors', 'irish factors', 'seai factors', 'irish emission factors', 'debra'], ids: ['which-factor-sets'], boost: 40 },
];

function scoreItem(item, q) {
  const itemQ = normalize(item.q);
  const qWords = expandQueryWords(q);
  const itemQWords = wordList(item.q);
  const itemAWords = wordList(item.a);

  let score = 0;

  // Exact phrase of the user's question appears in the item's question.
  if (q.norm.length >= 6 && itemQ.includes(q.norm)) score += 70;

  // Curated compound-term hints.
  for (const hint of PHRASE_HINTS) {
    if (hint.ids.includes(item.id) && hint.phrases.some((p) => q.norm.includes(p))) {
      score += hint.boost;
    }
  }

  const qOverlap = countOverlap(qWords, itemQWords);
  const aOverlap = countOverlap(qWords, itemAWords);

  // Question-title overlap is the primary signal.
  score += qOverlap * 8;
  // Fraction of the user's question found in the item's question.
  if (qWords.length > 0) score += 25 * (qOverlap / qWords.length);
  // Full recall of the user's question in the item's title.
  if (qOverlap > 0 && qOverlap === qWords.length) score += 15;
  // Answer-text overlap only matters when the question-title overlap is empty.
  if (qOverlap === 0) score += aOverlap * 2;

  return score;
}

// ---------------------------------------------------------------------------
// Intent responses (assistant-native, not FAQ items)
// ---------------------------------------------------------------------------

const SUGGESTED_QUESTIONS = [
  'How does CarbonTally work?',
  'What documents can CarbonTally process?',
  'What is human-assisted processing?',
  'Which emission factors are supported?',
  'How does traceability work?',
  'What reports are available?',
];

function intentResponse(name) {
  switch (name) {
    case 'greeting':
      return {
        answer: 'Hi, I\u2019m the CarbonTally Assistant. I can help you understand CarbonTally and how our processing service works — documents and data, extraction and OCR, mapping and emission factors, calculations, review and approval, evidence, traceability, reports and more.\n\nHere are a few questions to get you started:',
        source: SOURCE_ASSISTANT,
        category: null,
        id: null,
        related: [],
        suggestions: SUGGESTED_QUESTIONS.slice(0, 3),
      };
    case 'capabilities':
      return {
        answer: 'I can answer questions about CarbonTally and how the service works, for example:\n\n• How processing works, from source data to reports\n• Which documents and formats CarbonTally can process\n• Extraction, OCR and human review\n• Mapping and emission factors (UK DEFRA, Irish SEAI and custom factors)\n• Calculations, validation, review and quality control\n• Evidence, traceability and customer approval\n• Consultants, Processing Entities and assisted/managed processing\n• Security, data handling, reports and pricing\n\nI\u2019m the public assistant, so I can\u2019t see your account, documents or processing data. I also don\u2019t provide legal, audit or compliance assurance.',
        source: SOURCE_ASSISTANT,
        category: null,
        id: null,
        related: [],
        suggestions: SUGGESTED_QUESTIONS,
      };
    case 'contact':
      return {
        answer: 'For anything CarbonTally hasn\u2019t answered here, or for launch information, the team can help directly. You can contact CarbonTally through the contact page.',
        source: SOURCE_ASSISTANT,
        category: null,
        id: null,
        related: [],
        suggestions: ['How does CarbonTally work?', 'What does CarbonTally cost?'],
      };
    case 'thanks':
      return {
        answer: 'You\u2019re welcome. Is there anything else you\u2019d like to know about CarbonTally?',
        source: SOURCE_ASSISTANT,
        category: null,
        id: null,
        related: [],
        suggestions: [],
      };
    case 'account-data':
      return {
        answer: 'I\u2019m the public CarbonTally assistant, so I can\u2019t see your account, documents or processing data. I can explain how CarbonTally works in general. For anything about your own data — processing status, documents, approvals or reports — please contact CarbonTally.',
        source: SOURCE_ASSISTANT,
        category: null,
        id: null,
        related: [],
        suggestions: ['How does CarbonTally work?', 'How does traceability work?'],
      };
    default:
      return fallbackResponse();
  }
}

function fallbackResponse() {
  return {
    answer: 'I don\u2019t have enough information to answer that reliably. Please contact CarbonTally for confirmation.',
    source: SOURCE_ASSISTANT,
    category: null,
    id: null,
    related: [],
    suggestions: SUGGESTED_QUESTIONS.slice(0, 3),
  };
}

// Intent detection (run before FAQ retrieval).
const INTENTS = [
  {
    // Questions about the user's specific account state (their actual
    // processing, documents, approvals) — the public assistant has no access
    // to those, so it deflects to the contact path. Public-safe questions that
    // merely mention "my data" in general (e.g. "Is my data separated between
    // organisations?") are answered from the FAQ instead.
    name: 'account-data',
    test: (norm) =>
      /(where is my|when will my|why is my|how far along is my|is my processing|can you check my|can you see my|show my|what is my status|my processing status|my pending|my approvals|my approval|my invoice|my invoices|my results|my report|my reports|my account|my workspac)/.test(norm),
  },
  {
    name: 'greeting',
    test: (norm) => /^\s*(hi|hello|hey|hiya|howdy|good (morning|afternoon|evening))\b/.test(norm) || norm === 'hi' || norm === 'hello' || norm === 'hey',
  },
  {
    name: 'capabilities',
    test: (norm) => /\b(what can you do|what do you do|how can you help|what are you|who are you|what can i ask|help me understand)\b/.test(norm),
  },
  {
    name: 'contact',
    test: (norm) => /\b(contact|talk to (someone|a human|a person|the team)|speak to|phone|email address|customer support|support team|call us|get in touch)\b/.test(norm),
  },
  {
    name: 'thanks',
    test: (norm) => /\b(thanks|thank you|cheers)\b/.test(norm) && norm.split(' ').length <= 4,
  },
];

// ---------------------------------------------------------------------------
// Public interface
// ---------------------------------------------------------------------------

export function handleQuery(raw) {
  const q = analyzeQuery(raw);
  const norm = q.norm;

  if (!norm) return fallbackResponse();

  // Intents first.
  for (const intent of INTENTS) {
    if (intent.test(norm)) return intentResponse(intent.name);
  }

  // FAQ retrieval.
  const MIN_SCORE = 14;
  const scored = ALL_ITEMS.map((item) => ({ item, score: scoreItem(item, q) }))
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score);

  if (scored.length === 0 || scored[0].score < MIN_SCORE) {
    return fallbackResponse();
  }

  const best = scored[0].item;
  const related = scored
    .slice(1)
    .filter((s) => s.item.id !== best.id && s.score >= Math.max(MIN_SCORE, best.score * 0.5))
    .slice(0, 2)
    .map((s) => ({ id: s.item.id, q: s.item.q }));

  return {
    answer: best.a,
    source: SOURCE_FAQ,
    category: best.categoryTitle,
    id: best.id,
    related,
    suggestions: [],
  };
}

export { SOURCE_FAQ, SOURCE_ASSISTANT, SUGGESTED_QUESTIONS };
