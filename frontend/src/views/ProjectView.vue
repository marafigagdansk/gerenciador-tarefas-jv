<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, formatDate, formatFirstLastName, getInitials } from '../api'
import { useCompanyStore } from '../stores/company'
import { useTaskStore } from '../stores/task'
import { Gauge, CalendarDays, Trash2, Users, UserPlus } from 'lucide-vue-next'
import TaskWorkspace from '../components/TaskWorkspace.vue'
import ProjectAccessModal from '../components/ProjectAccessModal.vue'
import ProjectDeleteModal from '../components/ProjectDeleteModal.vue'

const route = useRoute()
const router = useRouter()
const company = useCompanyStore()
const taskStore = useTaskStore()

const project = ref(null)
const erro = ref('')
const acessoAberto = ref(false)
const modalExclusaoAberto = ref(false)

function onProjetoExcluido() {
  modalExclusaoAberto.value = false
  router.replace({ name: 'tasks', params: { companyId: company.companyId } })
}

const projectId = computed(() => Number(route.params.projectId))

async function carregarProjeto(id = projectId.value) {
  if (!id) return
  erro.value = ''
  try {
    project.value = await api(`/companies/${company.companyId}/projects/${id}`)
  } catch (err) {
    erro.value = err.message
    router.replace({ name: 'tasks', params: { companyId: company.companyId } })
  }
}

watch(projectId, (id) => {
  project.value = null
  carregarProjeto(id)
}, { immediate: true })

function onAcessoSalvo() {
  carregarProjeto()
}

function clicarEspacoColaboradores() {
  if (company.isMasterInCurrentCompany) {
    acessoAberto.value = true
  }
}

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


async function alternarArquivo() {
  const status = project.value.status === 'active' ? 'archived' : 'active'
  try {
    project.value = await company.updateProject(project.value.id, { status })
  } catch (err) {
    erro.value = err.message
  }
}

// ---------- Cabeçalho do projeto ----------
// Avanço = tarefas concluídas / total de tarefas do projeto (acompanha o quadro em tempo real)
const total = computed(() => taskStore.tasks.length)
const concluidas = computed(() => taskStore.tasks.filter((t) => t.status === 'done').length)
const percentual = computed(() => (total.value ? Math.round((concluidas.value / total.value) * 100) : 0))

function hojeStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const situacao = computed(() => {
  if (total.value > 0 && percentual.value === 100) return { label: 'Concluído', cls: 'badge-done' }
  const due = project.value.due_date
  if (!due) return { label: 'Sem previsão', cls: 'badge-muted' }
  if (due.split('T')[0] < hojeStr()) return { label: 'Atrasado', cls: 'badge-overdue' }
  return { label: 'No prazo', cls: 'badge-done' }
})
</script>

<template>
  <div v-if="project" :key="project.id">
    <div v-if="erro" class="alert-error" style="margin-bottom: 1rem">{{ erro }}</div>

    <header class="project-header">
      <div class="project-header-top">
        <div class="project-info">
          <div class="project-badges">
            <span class="badge" :class="situacao.cls">{{ situacao.label }}</span>
          </div>
          <h1>{{ project.name }}</h1>
          <p v-if="project.description" class="project-description">{{ project.description }}</p>

          <!-- Espaço interativo dos colaboradores do projeto -->
          <div
            class="project-collabs-bar"
            :class="{ 'is-clickable': company.isMasterInCurrentCompany }"
            :role="company.isMasterInCurrentCompany ? 'button' : undefined"
            :tabindex="company.isMasterInCurrentCompany ? 0 : undefined"
            @click="clicarEspacoColaboradores"
            @keydown.enter="clicarEspacoColaboradores"
            @keydown.space.prevent="clicarEspacoColaboradores"
            :title="company.isMasterInCurrentCompany ? 'Clique para gerenciar colaboradores e permissões de criação de tarefas' : 'Colaboradores com acesso a este projeto'"
          >
            <span class="collabs-label">
              <Users :size="13" />
              <span>Colaboradores:</span>
            </span>

            <div v-if="project.collaborators && project.collaborators.length" class="collabs-avatars">
              <div
                v-for="c in project.collaborators"
                :key="c.id"
                class="collab-avatar-circle"
                :style="avatarColorStyle(c.name)"
                :title="formatFirstLastName(c.name) + (c.can_create_tasks ? ' • Pode criar tarefas' : '')"
              >
                <span>{{ getInitials(c.name) }}</span>
                <span
                  v-if="c.can_create_tasks"
                  class="can-create-indicator"
                  title="Permissão para criar tarefas habilitada"
                ></span>
              </div>
            </div>

            <div v-else class="collabs-empty">
              <span class="collabs-empty-circle">
                <UserPlus v-if="company.isMasterInCurrentCompany" :size="12" />
                <span v-else>—</span>
              </span>
              <span class="collabs-empty-text">
                {{ company.isMasterInCurrentCompany ? 'Nenhum colaborador atribuído. Clique para gerenciar.' : 'Nenhum colaborador atribuído.' }}
              </span>
            </div>
          </div>
        </div>

        <div class="project-stats">
          <div class="stat-card">
            <span class="stat-label"><Gauge :size="13" /> Avanço</span>
            <strong class="stat-value">{{ percentual }}%</strong>
          </div>
          <div class="stat-card">
            <span class="stat-label"><CalendarDays :size="13" /> Previsão</span>
            <strong class="stat-value">{{ project.due_date ? formatDate(project.due_date) : '—' }}</strong>
          </div>
        </div>
      </div>

      <div class="project-progress-head">
        <span>Progresso Geral do Escopo</span>
        <strong>{{ percentual }}% Concluído</strong>
      </div>
      <div
        class="project-progress"
        role="progressbar"
        :aria-valuenow="percentual"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <span :style="{ width: percentual + '%' }"></span>
      </div>

      <div v-if="company.isMasterInCurrentCompany" class="project-tools">
        <button id="btn-acesso-projeto" class="btn btn-secondary btn-sm" @click="acessoAberto = true">Gerenciar acesso</button>
        <button id="btn-arquivar-projeto" class="btn btn-secondary btn-sm" @click="alternarArquivo">
          {{ project.status === 'active' ? 'Arquivar projeto' : 'Reativar projeto' }}
        </button>
        <button id="btn-excluir-projeto" class="btn btn-danger btn-sm" @click="modalExclusaoAberto = true">
          <Trash2 :size="14" /> Excluir projeto
        </button>
      </div>
    </header>

    <TaskWorkspace
      :project-id="project.id"
      kanban
      :show-title="false"
      :archived="project.status === 'archived'"
      :can-create="company.isMasterInCurrentCompany || Boolean(project.can_create_tasks)"
    />

    <ProjectAccessModal
      :is-open="acessoAberto"
      :project-id="project.id"
      @close="acessoAberto = false"
      @saved="onAcessoSalvo"
    />
    <ProjectDeleteModal
      :is-open="modalExclusaoAberto"
      :project="project"
      @close="modalExclusaoAberto = false"
      @deleted="onProjetoExcluido"
    />
  </div>
  <p v-else-if="!erro" class="loading-state">Carregando projeto...</p>
</template>

<style scoped>
.project-header {
  margin-bottom: 1.5rem;
  padding: 1.25rem 1.5rem 1.1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.project-header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}

.project-info {
  flex: 1;
  min-width: 260px;
}

.project-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}

.project-info h1 {
  font-size: 1.9rem;
  font-weight: 800;
  line-height: 1.15;
  color: var(--text-main);
  overflow-wrap: anywhere;
}

.project-description {
  margin-top: 0.6rem;
  max-width: 960px;
  font-size: 0.92rem;
  line-height: 1.5;
  color: var(--text-muted);
  overflow-wrap: anywhere;
  white-space: pre-line;
}

.project-collabs-bar {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.9rem;
  padding: 0.4rem 0.75rem;
  background: #F9FAFB;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  max-width: 100%;
  flex-wrap: wrap;
  transition: all 0.2s ease;
}

.project-collabs-bar.is-clickable {
  cursor: pointer;
}

.project-collabs-bar.is-clickable:hover {
  background: #F0FDFA;
  border-color: #5EEAD4;
  box-shadow: 0 2px 6px rgba(15, 118, 110, 0.08);
}

.collabs-label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.collabs-avatars {
  display: flex;
  align-items: center;
  padding-left: 4px;
}

.collab-avatar-circle {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  margin-left: -8px;
  border-radius: 50%;
  border: 2px solid #FFFFFF;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.15s ease, z-index 0.15s ease, box-shadow 0.15s ease;
  user-select: none;
}

.collab-avatar-circle:first-child {
  margin-left: 0;
}

.collab-avatar-circle:hover {
  transform: translateY(-2px) scale(1.1);
  z-index: 5;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
}

.can-create-indicator {
  position: absolute;
  bottom: -1px;
  right: -1px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #0F766E;
  border: 1.5px solid #FFFFFF;
}

.collabs-empty {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}

.collabs-empty-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1.5px dashed var(--border-color);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  background: #FFFFFF;
}

.collabs-empty-text {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-style: italic;
}

.project-stats {
  display: flex;
  gap: 0.75rem;
}

.stat-card {
  min-width: 140px;
  padding: 0.8rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  background: #F5F5F4;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.stat-label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.stat-value {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--text-main);
}

.project-progress-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.45rem;
  font-size: 0.74rem;
  color: var(--text-muted);
}

.project-progress-head strong {
  color: var(--text-main);
  font-weight: 700;
}

.project-progress {
  height: 7px;
  background: #E7E5E4;
  border-radius: 999px;
  overflow: hidden;
}

.project-progress span {
  display: block;
  height: 100%;
  background: #0F766E;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.project-tools {
  display: flex;
  gap: 0.6rem;
  justify-content: flex-end;
  margin-top: 1rem;
}
</style>
