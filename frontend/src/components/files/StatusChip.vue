<script setup lang="ts">
defineProps<{
  tone: 'success' | 'warning' | 'danger' | 'info' | 'knowledge' | 'muted'
  label: string
}>()
</script>

<template>
  <span
    class="status-chip-base"
    :class="{
      'border-#B8E5C8 bg-#EAF8EF text-#1F7A45': tone === 'success',
      'border-#F0D58B bg-#FFF7DF text-#936300': tone === 'warning',
      'border-#F5B5AF bg-#FFF0EE text-#B42318': tone === 'danger',
      'border-#CBD8FF bg-primarySoft text-primary': tone === 'info',
      'border-#DAD4FF bg-#F1EEFF text-knowledge': tone === 'knowledge',
      'border-line bg-muted text-sub': tone === 'muted',
    }"
  >
    {{ label }}
  </span>
</template>
