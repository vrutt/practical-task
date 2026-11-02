import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";
import simpleImportSort from "eslint-plugin-simple-import-sort";

const config = [
  ...nextVitals,
  ...nextTypescript,
  { ignores: [".next/**", "next-env.d.ts"] },
  {
    plugins: { "simple-import-sort": simpleImportSort },
    rules: { "simple-import-sort/imports": "error", "simple-import-sort/exports": "error" },
  },
];
export default config;
