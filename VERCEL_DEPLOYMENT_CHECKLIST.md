# Vercel Deployment Checklist

□ `npm run build` passes

□ TypeScript passes

□ Next.js passes

□ React Leaflet loads

□ Maps render

□ Environment variables configured

□ Production build verified

## Notes

- The frontend expects `NEXT_PUBLIC_API_BASE_URL` to point at the deployed backend.
- The map component is rendered client-side only through `next/dynamic` with `ssr: false`.
- The build was verified locally before writing this checklist.