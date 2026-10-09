// App.test.js — F-4 TOOLCHAIN REGRESSION GUARD (CT-MP-SUB-004 prod readiness).
//
// History: this file was the Create-React-App scaffold test
// (`expect(screen.getByText(/learn react/i))`), which asserted boilerplate text
// that does not exist in the product and additionally could not even LOAD,
// because `src/App.js` -> `react-router-dom` -> `react-router/dom` is a package
// `exports` SUBPATH that the Jest 27 resolver shipped with react-scripts@5 does
// not resolve ("Cannot find module 'react-router/dom'"). The scaffold assertion
// provided NO product coverage.
//
// Rendering the whole `src/App.js` entry point under this Jest 27 environment is
// not possible without unrelated, sweeping test-infrastructure changes: App
// transitively imports third-party packages shipped as untransformed ESM
// (axios, react-pdf/pdfjs, ...), which Jest cannot parse.
//
// The RELIABLE baseline established here is a focused guard over the exact thing
// that was broken — the react-router v7 module resolution + the jsdom globals it
// needs (see `package.json` → `jest.moduleNameMapper` and `src/setupTests.js`).
// If either regresses, THIS suite fails.
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Link } from 'react-router-dom';
import * as dom from 'react-router/dom';

function Home() {
  return <Link to="/manual-processing">Manual Processing</Link>;
}

function ManualProcessing() {
  return <h1>Manual Processing</h1>;
}

test('the react-router/dom subpath resolves under Jest (F-4 root cause)', () => {
  // `react-router-dom@7` unconditionally requires this subpath. This assertion
  // fails if the `jest.moduleNameMapper` mapping is removed.
  expect(typeof dom.RouterProvider).toBe('function');
});

test('react-router v7 loads and routes under the Jest jsdom environment', () => {
  // Loads the real react-router (TextEncoder/TextDecoder shim in setupTests.js).
  render(
    <MemoryRouter initialEntries={['/manual-processing']}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/manual-processing" element={<ManualProcessing />} />
      </Routes>
    </MemoryRouter>,
  );
  expect(
    screen.getByRole('heading', { level: 1, name: /manual processing/i }),
  ).toBeInTheDocument();
});

test('in-app links resolve to their target route', () => {
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/manual-processing" element={<ManualProcessing />} />
      </Routes>
    </MemoryRouter>,
  );
  expect(
    screen.getByRole('link', { name: /manual processing/i }),
  ).toHaveAttribute('href', '/manual-processing');
});

