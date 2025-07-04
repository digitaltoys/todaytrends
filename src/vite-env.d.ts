/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_COUCHDB_HOST: string
  readonly VITE_COUCHDB_USERNAME: string
  readonly VITE_COUCHDB_PASSWORD: string
  readonly VITE_COUCHDB_DB_NAME: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
