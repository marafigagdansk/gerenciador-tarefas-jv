<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ChevronDown, Check, Circle, AlertCircle } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, required: true },
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: 'Selecione...' },
  id: { type: String, default: '' },
  type: { type: String, default: 'default' }, // 'status', 'priority', 'default'
})

const emit = defineEmits(['update:modelValue', 'change'])

const isOpen = ref(false)
const containerRef = ref(null)

const normalizedOptions = computed(() => {
  return props.options.map((opt) => {
    if (typeof opt === 'string' || typeof opt === 'number') {
      return { value: opt, label: String(opt) }
    }
    return {
      value: opt.value ?? opt.id ?? opt.key,
      label: opt.label ?? opt.name ?? String(opt.value),
      badgeClass: opt.badgeClass,
      description: opt.description,
    }
  })
})

const selectedOption = computed(() => {
  return normalizedOptions.value.find((o) => String(o.value) === String(props.modelValue)) || null
})

function toggleDropdown() {
  if (props.disabled) return
  isOpen.value = !isOpen.value
}

function selectOption(opt) {
  emit('update:modelValue', opt.value)
  emit('change', opt.value)
  isOpen.value = false
}

function getBadgeClass(val) {
  if (props.type === 'status') {
    return `badge-${val}`
  }
  if (props.type === 'priority') {
    return `badge-${val}`
  }
  return ''
}

function getDotColor(val) {
  if (props.type === 'status') {
    const map = {
      todo: '#64748B',
      in_progress: '#2563EB',
      blocked: '#DC2626',
      done: '#16A34A',
    }
    return map[val] || '#64748B'
  }
  if (props.type === 'priority') {
    const map = {
      low: '#64748B',
      medium: '#D97706',
      high: '#DC2626',
    }
    return map[val] || '#64748B'
  }
  return '#0F766E'
}

function handleClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    isOpen.value = false
  }
}

function handleKeydown(e) {
  if (e.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div ref="containerRef" class="custom-select-container">
    <!-- Botão Gatilho do Select -->
    <button
      :id="id"
      type="button"
      class="select-trigger"
      :class="{ 'is-open': isOpen, 'is-disabled': disabled, 'has-selected': Boolean(selectedOption) }"
      :disabled="disabled"
      @click="toggleDropdown"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
    >
      <div class="trigger-value">
        <template v-if="selectedOption">
          <!-- Renderização com Badge para Status ou Prioridade -->
          <span
            v-if="type === 'status' || type === 'priority'"
            class="badge select-badge"
            :class="getBadgeClass(selectedOption.value)"
          >
            <span class="status-dot" :style="{ backgroundColor: getDotColor(selectedOption.value) }"></span>
            <span>{{ selectedOption.label }}</span>
          </span>

          <!-- Renderização Normal -->
          <span v-else class="normal-label">
            {{ selectedOption.label }}
          </span>
        </template>
        <span v-else class="placeholder-text">{{ placeholder }}</span>
      </div>

      <ChevronDown :size="16" class="select-chevron" :class="{ 'chevron-rotated': isOpen }" />
    </button>

    <!-- Dropdown Popover de Opções -->
    <transition name="dropdown-fade">
      <div v-if="isOpen" class="select-dropdown" role="listbox">
        <div
          v-for="opt in normalizedOptions"
          :key="opt.value"
          class="select-option"
          :class="{ 'is-selected': String(opt.value) === String(modelValue) }"
          role="option"
          :aria-selected="String(opt.value) === String(modelValue)"
          @click="selectOption(opt)"
        >
          <div class="option-content">
            <template v-if="type === 'status' || type === 'priority'">
              <span class="badge select-badge" :class="getBadgeClass(opt.value)">
                <span class="status-dot" :style="{ backgroundColor: getDotColor(opt.value) }"></span>
                <span>{{ opt.label }}</span>
              </span>
            </template>
            <template v-else>
              <span class="option-label">{{ opt.label }}</span>
            </template>
          </div>

          <Check v-if="String(opt.value) === String(modelValue)" :size="15" class="check-icon" />
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.custom-select-container {
  position: relative;
  width: 100%;
}

.select-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.45rem 0.85rem;
  background: var(--bg-input, #FFFFFF);
  border: 1px solid var(--border-color, #E7E5E4);
  border-radius: var(--radius-sm, 6px);
  color: var(--text-main, #1C1917);
  font-family: inherit;
  font-size: 0.92rem;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
  transition: all 0.15s ease;
  min-height: 40px;
}

.select-trigger:hover:not(:disabled) {
  border-color: var(--border-color-hover, #D6D3D1);
  background: #FAFAF9;
}

.select-trigger.is-open {
  border-color: var(--primary, #0F766E);
  box-shadow: 0 0 0 2px var(--primary-glow, rgba(15, 118, 110, 0.18));
  background: #FFFFFF;
}

.select-trigger.is-disabled {
  opacity: 0.6;
  background: #F5F5F4;
  cursor: not-allowed;
}

.trigger-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.select-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.22rem 0.6rem;
  border-radius: 6px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.normal-label {
  font-weight: 500;
  color: var(--text-main, #1C1917);
}

.placeholder-text {
  color: var(--text-muted, #78716C);
}

.select-chevron {
  color: var(--text-muted, #78716C);
  flex-shrink: 0;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.select-chevron.chevron-rotated {
  transform: rotate(180deg);
  color: var(--primary, #0F766E);
}

/* Dropdown Menu */
.select-dropdown {
  position: absolute;
  top: calc(100% + 5px);
  left: 0;
  right: 0;
  z-index: 70;
  max-height: 260px;
  overflow-y: auto;
  background: #FFFFFF;
  border: 1px solid var(--border-color, #E7E5E4);
  border-radius: var(--radius-md, 10px);
  box-shadow: var(--shadow-modal, 0 10px 25px -5px rgba(0, 0, 0, 0.12));
  padding: 0.35rem;
  user-select: none;
}

.select-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 0.65rem;
  border-radius: var(--radius-sm, 6px);
  cursor: pointer;
  transition: all 0.15s ease;
}

.select-option:hover {
  background: #F5F5F4;
}

.select-option.is-selected {
  background: #F0FDFA;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.option-label {
  font-size: 0.88rem;
  font-weight: 500;
  color: var(--text-main, #1C1917);
}

.check-icon {
  color: var(--primary, #0F766E);
  flex-shrink: 0;
}

/* Animações */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
