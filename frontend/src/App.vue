<script setup lang="ts">
import { dateZhCN, zhCN } from 'naive-ui'
import { RouterView } from 'vue-router'

import { naiveThemeOverrides } from '@/plugins/naive'
</script>

<template>
  <NConfigProvider :locale="zhCN" :date-locale="dateZhCN" :theme-overrides="naiveThemeOverrides">
    <NMessageProvider>
      <NDialogProvider>
        <RouterView />
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>
