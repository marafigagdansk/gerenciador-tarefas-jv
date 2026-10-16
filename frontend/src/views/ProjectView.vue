<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, formatDate } from '../api'
import { useCompanyStore } from '../stores/company'
import { useTaskStore } from '../stores/task'
import { Gauge, CalendarDays, Trash2 } from 'lucide-vue-next'
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

watch(projectId, async (id) => {
  project.value = null
  erro.value = ''
  try {
    project.value = await api(`/companies/${company.companyId}/projects/${id}`)
  } catch (err) {
    erro.value = err.message
    router.replace({ name: 'tasks', params: { companyId: company.companyId } })
  }
}, { immediate: true })

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

    <ProjectAccessModal :is-open="acessoAberto" :project-id="project.id" @close="acessoAberto = false" />
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
