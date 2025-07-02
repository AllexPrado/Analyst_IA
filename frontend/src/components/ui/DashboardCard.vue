<template>
  <div :class="[
    'rounded-xl overflow-hidden shadow-lg transition-all duration-200 transform hover:shadow-xl',
    'border border-opacity-10',
    backgroundColor
  ]">
    <!-- Cabeçalho -->
    <div class="px-6 py-4 flex items-center justify-between" :class="headerClass">
      <div class="flex items-center">
        <div v-if="icon" class="mr-3">
          <div class="p-2 rounded-full" :class="iconBackgroundClass">
            <font-awesome-icon :icon="icon" class="text-white text-lg" />
          </div>
        </div>
        <div>
          <h3 class="text-lg font-bold text-white">{{ title }}</h3>
          <p v-if="subtitle" class="text-sm text-gray-300">{{ subtitle }}</p>
        </div>
      </div>
      <div v-if="$slots.actions" class="actions">
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- Conteúdo -->
    <div :class="contentClass">
      <slot></slot>
    </div>

    <!-- Rodapé -->
    <div v-if="$slots.footer" :class="[footerClass, 'px-6 py-3 border-t', borderClass]">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  icon: {
    type: [String, Array],
    default: null
  },
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'primary', 'success', 'warning', 'danger', 'info'].includes(value)
  },
  transparent: {
    type: Boolean,
    default: false
  },
  contentPadding: {
    type: Boolean,
    default: true
  }
})

// Classes de cor baseadas na variante
const backgroundColor = computed(() => {
  if (props.transparent) return 'bg-transparent border-gray-700'
  
  switch (props.variant) {
    case 'primary': return 'bg-gradient-to-r from-blue-900 to-blue-800 border-blue-700'
    case 'success': return 'bg-gradient-to-r from-green-900 to-green-800 border-green-700'
    case 'warning': return 'bg-gradient-to-r from-yellow-900 to-yellow-800 border-yellow-700'
    case 'danger': return 'bg-gradient-to-r from-red-900 to-red-800 border-red-700'
    case 'info': return 'bg-gradient-to-r from-indigo-900 to-indigo-800 border-indigo-700'
    default: return 'bg-gray-900 border-gray-700'
  }
})

const headerClass = computed(() => {
  if (props.transparent) return 'border-b border-gray-700'
  
  switch (props.variant) {
    case 'primary': return 'bg-blue-900 bg-opacity-50'
    case 'success': return 'bg-green-900 bg-opacity-50'
    case 'warning': return 'bg-yellow-900 bg-opacity-50'
    case 'danger': return 'bg-red-900 bg-opacity-50'
    case 'info': return 'bg-indigo-900 bg-opacity-50'
    default: return 'bg-gray-800 bg-opacity-50'
  }
})

const iconBackgroundClass = computed(() => {
  switch (props.variant) {
    case 'primary': return 'bg-blue-700'
    case 'success': return 'bg-green-700'
    case 'warning': return 'bg-yellow-700'
    case 'danger': return 'bg-red-700'
    case 'info': return 'bg-indigo-700'
    default: return 'bg-gray-700'
  }
})

const contentClass = computed(() => {
  return props.contentPadding ? 'p-6' : ''
})

const footerClass = computed(() => {
  if (props.transparent) return 'bg-transparent'
  
  switch (props.variant) {
    case 'primary': return 'bg-blue-900 bg-opacity-30'
    case 'success': return 'bg-green-900 bg-opacity-30'
    case 'warning': return 'bg-yellow-900 bg-opacity-30'
    case 'danger': return 'bg-red-900 bg-opacity-30'
    case 'info': return 'bg-indigo-900 bg-opacity-30'
    default: return 'bg-gray-800 bg-opacity-30'
  }
})

const borderClass = computed(() => {
  switch (props.variant) {
    case 'primary': return 'border-blue-800'
    case 'success': return 'border-green-800'
    case 'warning': return 'border-yellow-800'
    case 'danger': return 'border-red-800'
    case 'info': return 'border-indigo-800'
    default: return 'border-gray-800'
  }
})
</script>
