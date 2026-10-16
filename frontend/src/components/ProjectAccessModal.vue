<script setup>
import { ref, computed, watch } from 'vue'
import { useCompanyStore } from '../stores/company'
import { getInitials } from '../api'
import { X, ShieldCheck } from 'lucide-vue-next'

const props = defineProps({ isOpen: Boolean, projectId: { type: Number, default: null } })
const emit = defineEmits(['close', 'saved'])

const company = useCompanyStore()
const colabAccess = ref({})
const erro = ref('')
const carregando = ref(false)

const collaborators = computed(() =>
  company.members.filter((m) => m.role === 'collaborator' && m.is_active)
)

const AVATAR_PALETTES = [
  { bg: '#EFF6FF', text: '#1D4ED8', border: '#BFDBFE' },
  { bg: '#F0FDFA', text: '#0F766E', border: '#99F6E4' },
  { bg: '#F5F3FF', text: '#6D28D9', border: '#DDD6FE' },
  { bg: '#FFFBEB', text: '#B45309', border: '#FDE68A' },
  { bg: '#ECFDF5', text: '#047857', border: '#A7F3D0' },
  { bg: '#FDF2F8', text: '#BE185D', border: '#FBCFE8' },
  { bg: '#F8FAFC', text: '#334155', border: '#CBD5E1' },
]

function avatarColorStyle(name) {
  let hash = 0
  const str = String(name || '')
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i)
    hash |= 0
  }
  const item = AVATAR_PALETTES[Math.abs(hash) % AVATAR_PALETTES.length]
  return {
    backgroundColor: item.bg,
    color: item.text,
    borderColor: item.border,
  }
}


watch(() => props.isOpen, async (open) => {
  if (!open) return
  erro.value = ''
  try {
    if (!company.members || company.members.length === 0) {
      await company.fetchMembers()
    }
    const data = await company.getVisibility(props.projectId)
    const items = data.items || []
    colabAccess.value = {}
    collaborators.value.forEach((m) => {
      const found = items.find((it) => it.membership_id === m.id)
      if (found) {
        colabAccess.value[m.id] = { selected: true, canCreate: Boolean(found.can_create_tasks) }
      } else if (data.membership_ids && data.membership_ids.includes(m.id)) {
        colabAccess.value[m.id] = { selected: true, canCreate: false }
      } else {
        colabAccess.value[m.id] = { selected: false, canCreate: false }
      }
    })
  } catch (err) {
    erro.value = err.message
  }
})

function isSelected(id) {
  return Boolean(colabAccess.value[id]?.selected)
}

function canCreate(id) {
  return Boolean(colabAccess.value[id]?.canCreate)
}

function toggleAccess(id, checked) {
  if (!colabAccess.value[id]) {
    colabAccess.value[id] = { selected: false, canCreate: false }
  }
  colabAccess.value[id].selected = checked
  if (!checked) {
    colabAccess.value[id].canCreate = false
  }
}

function toggleCanCreate(id, checked) {
  if (!colabAccess.value[id]) {
    colabAccess.value[id] = { selected: false, canCreate: false }
  }
  colabAccess.value[id].canCreate = checked
  if (checked) {
    colabAccess.value[id].selected = true
  }
}

async function salvar() {
  erro.value = ''
  carregando.value = true
  try {
    const items = collaborators.value
      .filter((m) => colabAccess.value[m.id]?.selected)
      .map((m) => ({
        membership_id: m.id,
        can_create_tasks: Boolean(colabAccess.value[m.id]?.canCreate),
      }))

    await company.setVisibility(props.projectId, items)
    await company.fetchProjects()
    emit('saved')
    emit('close')
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="emit('close')">
    <div class="modal-box">
      <div class="modal-header">
        <h3>Acesso ao Projeto</h3>
        <button class="btn-icon" @click="emit('close')" aria-label="Fechar">
          <X :size="20" />
        </button>
      </div>
      <form @submit.prevent="salvar" class="modal-body">
        <div v-if="erro" class="alert-error">{{ erro }}</div>
        <p class="hint" style="margin-bottom: 0.75rem">
          Colaboradores marcados enxergam este projeto e suas tarefas. Marque <strong>Cria Tarefas</strong> para permitir que criem tarefas no projeto.
        </p>
        <div class="check-list" style="max-height: 280px">
          <div v-for="m in collaborators" :key="m.id" class="collaborator-access-item">
            <label class="check-row access-toggle">
              <input
                type="checkbox"
                :checked="isSelected(m.id)"
                @change="toggleAccess(m.id, $event.target.checked)"
              />
              <span class="member-avatar-mini" :style="avatarColorStyle(m.name)">
                {{ getInitials(m.name) }}
              </span>
              <span class="member-name">{{ m.name }}</span>
            </label>
            <label
              class="check-row perm-badge"
              :class="{ disabled: !isSelected(m.id) }"
              :title="!isSelected(m.id) ? 'Dê acesso ao colaborador para habilitar criação de tarefas' : 'Permitir que este colaborador crie tarefas neste projeto'"
            >
              <input
                type="checkbox"
                :checked="canCreate(m.id)"
                :disabled="!isSelected(m.id)"
                @change="toggleCanCreate(m.id, $event.target.checked)"
              />
              <span>Cria Tarefas</span>
            </label>
          </div>
          <span v-if="collaborators.length === 0" class="hint">Nenhum colaborador cadastrado.</span>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="emit('close')">Cancelar</button>
          <button id="btn-salvar-acesso" type="submit" class="btn btn-primary" :disabled="carregando">Salvar acesso</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.collaborator-access-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.4rem 0.5rem;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}

.collaborator-access-item:hover {
  background: rgba(0, 0, 0, 0.03);
}

.access-toggle {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.member-avatar-mini {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.member-name {
  font-weight: 500;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.perm-badge {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.82rem;
  font-weight: 500;
  padding: 0.25rem 0.55rem;
  border-radius: var(--radius-sm);
  background: #ffffff;
  border: 1px solid var(--border-color);
  color: var(--text-main);
  user-select: none;
  cursor: pointer;
  white-space: nowrap;
}

.perm-badge.disabled {
  opacity: 0.45;
  cursor: not-allowed;
  background: transparent;
  border-color: transparent;
}
</style>
