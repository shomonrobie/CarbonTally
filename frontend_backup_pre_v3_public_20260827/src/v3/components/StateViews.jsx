// frontend/src/v3/components/StateViews.jsx
// Compatibility re-export. The shared LOADING / ERROR / EMPTY / PERMISSION
// state primitives now live in ./ui/StateViews (D29/F3, D21). Existing imports
// of `../components/StateViews` keep working unchanged.
export { LoadingState, ErrorState, EmptyState, PermissionState } from './ui/StateViews';

