// frontend/src/v3/customer/ProcessingItemPage.jsx
// CL-54 — routed customer item workspace at /processing/:itemId.
// Deep-linkable and refresh-safe (the item id lives in the URL).
import React from 'react';
import { useParams } from 'react-router-dom';
import ProcessingItemWorkspace from './ProcessingItemWorkspace';

export default function ProcessingItemPage() {
  const { itemId } = useParams();
  return <ProcessingItemWorkspace itemId={itemId} />;
}
