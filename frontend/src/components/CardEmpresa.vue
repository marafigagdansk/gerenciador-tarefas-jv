<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { formatDoc, ROLE_LABELS } from '../api'
import { ArrowRight, MoreVertical, Pencil, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  membership: { type: Object, required: true },
})

const emit = defineEmits(['editar', 'excluir'])

const menuAberto = ref(false)

function toggleMenu(e) {
  menuAberto.value = !menuAberto.value
}

function fecharMenu() {
  menuAberto.value = false
}

function onDocClick(e) {
  if (menuAberto.value && !e.target.closest('.empresa-menu-container')) {
    fecharMenu()
  }
}

onMounted(() => {
  window.addEventListener('click', onDocClick)
})

onUnmounted(() => {
  window.removeEventListener('click', onDocClick)
})

function onEditar() {
  fecharMenu()
  emit('editar', props.membership)
}

function onExcluir() {
  fecharMenu()
  emit('excluir', props.membership)
}
</script>

<template>
  <RouterLink
    :to="`/companies/${membership.company_id}/tasks`"
    class="empresa-card"
  >
    <div class="top">
      <h3 :title="membership.company_name">{{ membership.company_name }}</h3>
      <div class="top-actions">
        <span class="badge" :class="`badge-${membership.role}`">{{ ROLE_LABELS[membership.role] }}</span>
        
        <!-- Menu de 3 pontinhos exclusivo para login Master da empresa -->
        <div v-if="membership.role === 'master'" class="empresa-menu-container" @click.prevent.stop>
          <button
            type="button"
            class="btn-icon btn-menu"
            :class="{ active: menuAberto }"
            title="Opções da empresa"
            aria-label="Opções da empresa"
            @click.prevent.stop="toggleMenu"
          >
            <MoreVertical :size="17" />
          </button>
          <div v-if="menuAberto" class="dropdown-menu" @click.prevent.stop>
            <button type="button" class="menu-item" @click.prevent.stop="onEditar">
              <Pencil :size="14" />
              Editar dados
            </button>
            <button type="button" class="menu-item menu-item-danger" @click.prevent.stop="onExcluir">
              <Trash2 :size="14" />
              Excluir empresa
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="doc">
      <span class="doc-label">{{ membership.cnpj.length > 11 ? 'CNPJ' : 'CPF' }}</span>
      {{ formatDoc(membership.cnpj) }}
    </div>
    <span class="enter">
      Entrar
      <ArrowRight :size="15" />
    </span>
  </RouterLink>
</template>

<style scoped>
.empresa-card {
  text-decoration: none;
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
  width: 100%;
  user-select: none;
  -webkit-user-select: none;
  transition: border-color 0.15s ease, background-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.empresa-card:hover {
  border-color: var(--border-color-hover);
  background: var(--bg-card-hover);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
}

.empresa-card:active {
  transform: translateY(0);
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
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: #a5b4fc;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.empresa-menu-container {
  position: relative;
  display: flex;
  align-items: center;
}

.btn-menu {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-menu:hover,
.btn-menu.active {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.1);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.35rem;
  background: #1e293b;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
  min-width: 155px;
  z-index: 30;
  padding: 0.35rem;
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-main);
  background: transparent;
  border: none;
  border-radius: 4px;
  width: 100%;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.menu-item-danger {
  color: #f87171;
}

.menu-item-danger:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}
</style>
