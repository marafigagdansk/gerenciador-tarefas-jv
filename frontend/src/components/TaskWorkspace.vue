<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTaskStore } from '../stores/task'
import { useCompanyStore } from '../stores/company'
import { useNotificationStore } from '../stores/notification'
import { STATUS_LABELS, PRIORITY_LABELS, formatDate } from '../api'
import {
  Calendar, CalendarOff, Plus, UserPlus, Check, CheckSquare,
  MoreVertical, Trash2, FolderGit2, User, Layers
} from 'lucide-vue-next'
import TaskFormModal from './TaskFormModal.vue'
import TaskDetailModal from './TaskDetailModal.vue'
import TaskDeleteModal from './TaskDeleteModal.vue'
import KanbanBoard from './KanbanBoard.vue'

const props = defineProps({
  projectId: { type: Number, default: null },
  title: String,
  subtitle: String,
  archived: Boolean,
  kanban: Boolean,
  showTitle: { type: Boolean, default: true },
  canCreate: { type: Boolean, default: true },
})

const store = useTaskStore()
const company = useCompanyStore()
const notifStore = useNotificationStore()

const filtro = ref('all')
const formAberto = ref(false)
const abertaId = ref(null)
const erro = ref('')

const menuAbertoId = ref(null)
const tarefaParaExcluir = ref(null)
const deleteModalAberto = ref(false)

const myId = computed(() => company.activeMembership?.id ?? null)

function souResponsavel(t) {
  return t.assignees.some((a) => a.membership_id === myId.value)
}

// ---------- Filtros rápidos por botões (Tarefas Gerais) ----------
const filterAssigned = ref(false)
const filterCreated = ref(false)
const selectedProjectIds = ref([]) // array de (number | 'none')

const isAllActive = computed(() =>
  !filterAssigned.value && !filterCreated.value && selectedProjectIds.value.length === 0
)

function selectAll() {
  filterAssigned.value = false
  filterCreated.value = false
  selectedProjectIds.value = []
}

function toggleAssigned() {
  filterAssigned.value = !filterAssigned.value
}

function toggleCreated() {
  filterCreated.value = !filterCreated.value
}

function toggleProject(pid) {
  const idx = selectedProjectIds.value.indexOf(pid)
  if (idx === -1) {
    selectedProjectIds.value.push(pid)
  } else {
    selectedProjectIds.value.splice(idx, 1)
  }
}

function isProjectSelected(pid) {
  return selectedProjectIds.value.includes(pid)
}

const availableProjects = computed(() =>
  company.projects.filter((p) => p.status === 'active')
)

const countAll = computed(() => store.tasks.length)
const countAssigned = computed(() => store.tasks.filter((t) => souResponsavel(t)).length)
const countCreated = computed(() => store.tasks.filter((t) => t.created_by_membership_id === myId.value).length)
const countUnassignedProject = computed(() => store.tasks.filter((t) => t.project_id === null).length)

function countByProject(pid) {
  return store.tasks.filter((t) => t.project_id === pid).length
}

const tarefasFiltradas = computed(() => {
  if (isAllActive.value) {
    return store.tasks
  }

  return store.tasks.filter((t) => {
    // 1. Filtro de Projeto (se algum selecionado)
    if (selectedProjectIds.value.length > 0) {
      const matchProject = selectedProjectIds.value.some((pid) => {
        if (pid === 'none') {
          return t.project_id === null
        }
        return t.project_id === pid
      })
      if (!matchProject) return false
    }

    // 2. Filtro Pessoal (se algum selecionado)
    const hasPersonalFilter = filterAssigned.value || filterCreated.value
    if (hasPersonalFilter) {
      const isAssigned = souResponsavel(t)
      const isCreated = t.created_by_membership_id === myId.value

      if (filterAssigned.value && filterCreated.value) {
        if (!isAssigned && !isCreated) return false
      } else if (filterAssigned.value) {
        if (!isAssigned) return false
      } else if (filterCreated.value) {
        if (!isCreated) return false
      }
    }

    return true
  })
})

const visiveis = computed(() =>
  filtro.value === 'all'
    ? tarefasFiltradas.value
    : tarefasFiltradas.value.filter((t) => t.status === filtro.value)
)
const aberta = computed(() => store.tasks.find((t) => t.id === abertaId.value) || null)

function podeExcluir(t) {
  return t.created_by_membership_id === myId.value || company.isMasterInCurrentCompany
}

function toggleMenu(taskId) {
  menuAbertoId.value = menuAbertoId.value === taskId ? null : taskId
}

function fecharMenu() {
  menuAbertoId.value = null
}

function abrirModalExclusao(t) {
  fecharMenu()
  abertaId.value = null
  tarefaParaExcluir.value = t
  deleteModalAberto.value = true
}

function onTarefaExcluida(taskId) {
  abertaId.value = null
  tarefaParaExcluir.value = null
  deleteModalAberto.value = false
}

function onDocClick(e) {
  if (menuAbertoId.value && !e.target.closest('.task-menu-container')) {
    fecharMenu()
  }
}

onMounted(async () => {
  window.addEventListener('click', onDocClick)
  store.tasks = []
  try {
    await store.fetchTasks(props.projectId)
  } catch (err) {
    erro.value = err.message
  }
  if (!company.projects.length) {
    company.fetchProjects().catch(() => {})
  }
})

onUnmounted(() => {
  window.removeEventListener('click', onDocClick)
})

function hojeStr() {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function isAtrasada(task) {
  if (!task.due_date || task.status === 'done') return false
  const due = task.due_date.split('T')[0]
  return due < hojeStr()
}

async function pegar(t) {
  try {
    await store.claimTask(t.id, props.projectId)
    notifStore.fetchOverviewRadar(company.companyId)
  } catch (err) {
    erro.value = err.message
  }
}

async function onMover({ status, ids }) {
  erro.value = ''
  try {
    // Mescla tarefas da coluna destino que estavam ocultas pelo filtro
    const colTasksAll = store.tasks.filter((t) => t.status === status)
    const colTaskIdsAll = colTasksAll.map((t) => t.id)
    const hiddenIds = colTaskIdsAll.filter((id) => !ids.includes(id))
    const finalIds = [...ids, ...hiddenIds]
    await store.reorderTasks(status, finalIds, props.projectId)
    notifStore.fetchOverviewRadar(company.companyId)
  } catch (err) {
    erro.value = err.message
  }
}

function abrirTarefa(t) {
  if (!t) return
  abertaId.value = typeof t === 'object' ? t.id : Number(t)
}

defineExpose({
  abrirTarefa,
})
</script>

<template>
  <section>
    <div class="page-header" :class="{ 'page-header-actions': !showTitle }">
      <div v-if="showTitle">
        <h1>{{ title }}</h1>
        <p class="subtitle">{{ subtitle }}</p>
      </div>
      <button v-if="!archived && canCreate" id="btn-nova-tarefa" class="btn btn-primary" @click="formAberto = true">
        <Plus :size="16" />
        Nova Tarefa
      </button>
    </div>

    <div v-if="archived" class="alert-info" style="margin-bottom: 1rem">Projeto arquivado: não aceita novas tarefas.</div>
    <div v-if="erro" class="alert-error" style="margin-bottom: 1rem">{{ erro }}</div>

    <!-- Barra de Filtros Rápidos (apenas em Tarefas Gerais) -->
    <div v-if="projectId === null" class="filter-pills-bar" role="toolbar" aria-label="Filtros rápidos de tarefas">
      <div class="filter-pills-group">
        <button
          type="button"
          class="filter-pill"
          :class="{ active: isAllActive }"
          @click="selectAll"
        >
          <span>Todas</span>
          <span class="pill-count">{{ countAll }}</span>
        </button>

        <button
          type="button"
          class="filter-pill"
          :class="{ active: filterAssigned }"
          @click="toggleAssigned"
        >
          <User :size="13" />
          <span>Atribuídas a mim</span>
          <span class="pill-count">{{ countAssigned }}</span>
        </button>

        <button
          type="button"
          class="filter-pill"
          :class="{ active: filterCreated }"
          @click="toggleCreated"
        >
          <CheckSquare :size="13" />
          <span>Criadas por mim</span>
          <span class="pill-count">{{ countCreated }}</span>
        </button>
      </div>

      <div v-if="countUnassignedProject > 0 || availableProjects.length > 0" class="filter-pills-divider" />

      <div v-if="countUnassignedProject > 0 || availableProjects.length > 0" class="filter-pills-group">
        <button
          v-if="countUnassignedProject > 0"
          type="button"
          class="filter-pill"
          :class="{ active: isProjectSelected('none') }"
          @click="toggleProject('none')"
        >
          <Layers :size="13" />
          <span>Sem projeto</span>
          <span class="pill-count">{{ countUnassignedProject }}</span>
        </button>

        <button
          v-for="p in availableProjects"
          :key="p.id"
          type="button"
          class="filter-pill"
          :class="{ active: isProjectSelected(p.id) }"
          @click="toggleProject(p.id)"
        >
          <FolderGit2 :size="13" />
          <span>{{ p.name }}</span>
          <span class="pill-count">{{ countByProject(p.id) }}</span>
        </button>
      </div>
    </div>

    <div v-if="!kanban" class="filters" role="tablist">
      <button
        class="filter"
        :class="{ active: filtro === 'all' }"
        @click="filtro = 'all'"
      >
        Todas ({{ tarefasFiltradas.length }})
      </button>
      <button
        v-for="(label, key) in STATUS_LABELS"
        :key="key"
        class="filter"
        :class="{ active: filtro === key }"
        @click="filtro = key"
      >
        {{ label }}
      </button>
    </div>

    <p v-if="store.loading" class="loading-state">Carregando tarefas...</p>
    <KanbanBoard
      v-else-if="kanban"
      :tasks="tarefasFiltradas"
      :my-id="myId"
      :is-master="company.isMasterInCurrentCompany"
      @open="(t) => (abertaId = t.id)"
      @claim="pegar"
      @move="onMover"
      @denied="(msg) => (erro = msg)"
    />
    <div v-else-if="visiveis.length === 0" class="empty-box">
      <h3>Nenhuma tarefa aqui</h3>
      <p>Use "+ Nova Tarefa" para criar a primeira.</p>
    </div>

    <ul v-else class="task-list">
      <li v-for="t in visiveis" :key="t.id" class="task-card" @click="abertaId = t.id">
        <div class="task-main">
          <h3>{{ t.title }}</h3>
          <div class="meta">
            <span v-if="t.project_name" class="badge badge-project" :title="`Projeto: ${t.project_name}`">
              <FolderGit2 :size="13" />
              {{ t.project_name }}
            </span>
            <span class="badge" :class="`badge-${t.status}`">{{ STATUS_LABELS[t.status] }}</span>
            <span class="badge" :class="`badge-${t.priority}`">Prioridade {{ PRIORITY_LABELS[t.priority] }}</span>
            <span
              v-if="t.due_date"
              class="badge"
              :class="isAtrasada(t) ? 'badge-overdue' : 'badge-due'"
              :title="isAtrasada(t) ? 'Tarefa com prazo expirado' : 'Prazo de conclusão'"
            >
              <Calendar :size="13" />
              {{ formatDate(t.due_date) }}{{ isAtrasada(t) ? ' (Atrasada)' : '' }}
            </span>
            <span v-else class="badge badge-muted" title="Sem prazo definido">
              <CalendarOff :size="13" />
              Data indefinida
            </span>
            <span v-if="t.subtasks.length" class="badge badge-muted">
              <CheckSquare :size="13" />
              Sub-tarefas {{ t.subtasks.filter((s) => s.is_completed).length }}/{{ t.subtasks.length }}
            </span>
          </div>
          <p class="assignees">
            <template v-if="t.assignees.length">Responsáveis: {{ t.assignees.map((a) => a.name).join(', ') }}</template>
            <template v-else>Sem responsável</template>
          </p>
        </div>
        <div class="task-action" @click.stop>
          <button v-if="!souResponsavel(t)" class="btn btn-primary btn-sm" @click="pegar(t)">
            <UserPlus :size="14" />
            Pegar Tarefa
          </button>
          <button v-else class="btn btn-secondary btn-sm" disabled>
            <Check :size="14" />
            Já atribuído
          </button>

          <!-- 3 Pontinhos com opção de excluir para o criador da tarefa (ou Master) -->
          <div v-if="podeExcluir(t)" class="task-menu-container">
            <button
              class="btn-icon btn-menu"
              :class="{ active: menuAbertoId === t.id }"
              title="Mais opções da tarefa"
              aria-label="Mais opções da tarefa"
              @click="toggleMenu(t.id)"
            >
              <MoreVertical :size="17" />
            </button>
            <div v-if="menuAbertoId === t.id" class="task-dropdown-menu">
              <button class="menu-item menu-item-danger" @click="abrirModalExclusao(t)">
                <Trash2 :size="14" />
                Excluir tarefa
              </button>
            </div>
          </div>
        </div>
      </li>
    </ul>

    <TaskFormModal
      :is-open="formAberto"
      :project-id="projectId"
      @close="formAberto = false; notifStore.fetchOverviewRadar(company.companyId)"
    />
    <TaskDetailModal
      v-if="aberta"
      :task="aberta"
      :scope-project-id="projectId"
      @close="abertaId = null; notifStore.fetchOverviewRadar(company.companyId)"
      @request-delete="abrirModalExclusao"
    />
    <TaskDeleteModal
      :is-open="deleteModalAberto"
      :task="tarefaParaExcluir"
      @close="deleteModalAberto = false"
      @deleted="onTarefaExcluida"
    />
  </section>
</template>

<style scoped>
.page-header-actions {
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.filter {
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-muted);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
  cursor: pointer;
  transition: all 0.15s ease;
}

.filter:hover {
  color: var(--text-main);
  background: #F5F5F4;
  border-color: #D6D3D1;
}

.filter.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  box-shadow: var(--shadow-xs);
}

.task-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.task-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.task-card:hover {
  border-color: #D6D3D1;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
}

.task-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.task-main h3 {
  font-size: 1.02rem;
  overflow-wrap: anywhere;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.assignees {
  font-size: 0.84rem;
  color: var(--text-muted);
}

.task-action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.task-menu-container {
  position: relative;
  display: flex;
  align-items: center;
}

.btn-menu {
  width: 32px;
  height: 32px;
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

.task-dropdown-menu {
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
  padding: 0.55rem 0.75rem;
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

/* ---------- Filtros Rápidos (Pills / Botões) ---------- */
.filter-pills-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  padding: 0.55rem 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.filter-pills-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.filter-pills-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
  margin: 0 0.25rem;
}

.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.75rem;
  font-family: inherit;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-canvas);
  border: 1px solid var(--border-color);
  border-radius: 9999px;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s ease;
}

.filter-pill:hover {
  background: #E7E5E4;
  color: var(--text-main);
  border-color: #D6D3D1;
}

.filter-pill.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #FFFFFF;
  box-shadow: 0 1px 3px rgba(15, 118, 110, 0.25);
}

.filter-pill.active:hover {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
}

.pill-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.15rem;
  height: 1.15rem;
  padding: 0 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  border-radius: 9999px;
  background: rgba(0, 0, 0, 0.06);
  color: inherit;
  line-height: 1;
}

.filter-pill.active .pill-count {
  background: rgba(255, 255, 255, 0.25);
  color: #FFFFFF;
}

.filter-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2.5rem 1.5rem;
  background: var(--bg-card);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
  text-align: center;
  color: var(--text-muted);
}
</style>
