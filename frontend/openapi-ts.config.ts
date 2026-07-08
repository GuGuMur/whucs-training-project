import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: 'src/client/openapi/workspace.openapi.json',
  output: 'src/client/generated',
})
