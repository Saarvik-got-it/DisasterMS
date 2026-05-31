# Deployment Audit

## 1. Root Cause Of The Original Failure

The Vercel build failed during TypeScript checking in `frontend/src/components/dashboard/map-inner.tsx` because a local ambient declaration file, `frontend/src/types/leaflet.d.ts`, was overriding the real `@types/leaflet` package.

That shim caused React-Leaflet's `TileLayerProps` to lose the `attribution` prop shape that should come from the installed Leaflet types.

## 2. Files Modified

- [frontend/package.json](frontend/package.json)
- [frontend/src/components/dashboard/map-inner.tsx](frontend/src/components/dashboard/map-inner.tsx)
- [frontend/src/types/leaflet.d.ts](frontend/src/types/leaflet.d.ts) deleted

## 3. All Deployment Issues Discovered

- The local `leaflet.d.ts` shim broke the real `react-leaflet` / `leaflet` type definitions.
- No other blocking build issues were found in the frontend audit.

Audit checks performed:

- Verified `react-leaflet` version: `5.0.0`
- Verified `leaflet` version: `1.9.4`
- Verified `@types/leaflet` version: `1.9.21`
- Verified `TileLayerProps` comes from `TileLayerOptions` plus `LayerProps` in the installed package declarations.
- Confirmed `MapPicker` uses `next/dynamic` with `ssr: false`, which is the correct Leaflet SSR handling.
- Confirmed browser-only APIs like `navigator.geolocation` are inside client components.
- Confirmed `NEXT_PUBLIC_*` access is used only in client-side code paths.

## 4. Fixes Applied

- Removed the conflicting local Leaflet declaration file.
- Restored the frontend manifest to use the published `@types/leaflet` package.
- Kept the map implementation unchanged in behavior and let the real type definitions drive the JSX props.

## 5. Remaining Risks

- Vercel still requires the correct production environment variables to be configured.
- The backend and external APIs remain runtime dependencies, so availability issues there can still affect production behavior.
- Leaflet tiles and Nominatim depend on third-party services.

## 6. Build Output Summary

Local verification command:

- `npm run build`

Result:

- Next.js production build completed successfully.
- TypeScript checking passed.
- Static generation completed successfully for all frontend routes.

Routes built:

- `/`
- `/history`
- `/settings`
- `/_not-found`
