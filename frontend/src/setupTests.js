// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// F-4 — react-router v7 (7.18.x) touches `TextEncoder`/`TextDecoder` at module
// load time. Jest 27's jsdom environment does not expose them as globals, so any
// suite that loads the real `react-router-dom` fails with
// "ReferenceError: TextEncoder is not defined". These are Node built-ins; wiring
// them into the jsdom global scope is a test-environment shim only and does not
// change application behaviour.
import { TextDecoder, TextEncoder } from 'util';

if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder;
}
if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = TextDecoder;
}
