<script setup lang="ts">
import { dateZhCN, zhCN } from 'naive-ui'
import { RouterView } from 'vue-router'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import { naiveThemeOverrides } from '@/plugins/naive'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('json', json)
</script>

<template>
  <NConfigProvider :locale="zhCN" :date-locale="dateZhCN" :theme-overrides="naiveThemeOverrides" :hljs="hljs">
    <NMessageProvider>
      <NDialogProvider>
        <RouterView />
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>
