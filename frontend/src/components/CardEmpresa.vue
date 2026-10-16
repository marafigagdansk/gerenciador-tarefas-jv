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
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  transition: border-color 0.15s ease, background-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.empresa-card:hover {
  border-color: #D6D3D1;
  background: var(--bg-card);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.08);
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
  color: var(--text-main);
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
  color: var(--primary);
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
  background: #F5F5F4;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.35rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
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
  background: #F5F5F4;
}

.menu-item-danger {
  color: #B91C1C;
}

.menu-item-danger:hover {
  background: #FEF2F2;
  color: #991B1B;
}
</style>
