<script setup>
import { formatDoc, ROLE_LABELS } from '../api'

defineProps({
  membership: { type: Object, required: true },
})
const emit = defineEmits(['select'])
</script>

<template>
  <button class="empresa-card" type="button" @click="emit('select', membership)">
    <div class="top">
      <h3 :title="membership.company_name">{{ membership.company_name }}</h3>
      <span class="badge" :class="`badge-${membership.role}`">{{ ROLE_LABELS[membership.role] }}</span>
    </div>
    <div class="doc">
      <span class="doc-label">{{ membership.cnpj.length > 11 ? 'CNPJ' : 'CPF' }}</span>
      {{ formatDoc(membership.cnpj) }}
    </div>
    <span class="enter">Entrar &rarr;</span>
  </button>
</template>

<style scoped>
.empresa-card {
  text-align: left;
  font-family: inherit;
  color: inherit;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.empresa-card:hover {
  border-color: var(--border-color-hover);
  background: var(--bg-card-hover);
}

.top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
}

h3 {
  font-size: 1.1rem;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.doc {
  font-size: 0.88rem;
  color: var(--text-muted);
}

.doc-label {
  font-weight: 700;
  margin-right: 0.35rem;
  color: var(--text-subtle);
}

.enter {
  font-size: 0.88rem;
  font-weight: 600;
  color: #a5b4fc;
}
</style>
