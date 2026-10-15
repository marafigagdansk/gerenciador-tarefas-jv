<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTaskStore } from '../stores/task'
import { useCompanyStore } from '../stores/company'
import { STATUS_LABELS, PRIORITY_LABELS, formatDate } from '../api'
import { Calendar, CalendarOff, Plus, UserPlus, Check, CheckSquare, MoreVertical, Trash2 } from 'lucide-vue-next'
import TaskFormModal from './TaskFormModal.vue'
import TaskDetailModal from './TaskDetailModal.vue'
import TaskDeleteModal from './TaskDeleteModal.vue'

const props = defineProps({
  projectId: { type: Number, default: null },
  title: String,
  subtitle: String,
  archived: Boolean,
})

const store = useTaskStore()
const company = useCompanyStore()

const filtro = ref('all')
const formAberto = ref(false)
const abertaId = ref(null)
const erro = ref('')

const menuAbertoId = ref(null)
const tarefaParaExcluir = ref(null)
const deleteModalAberto = ref(false)

const myId = computed(() => company.activeMembership?.id ?? null)

const visiveis = computed(() =>
  filtro.value === 'all' ? store.tasks : store.tasks.filter((t) => t.status === filtro.value)
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
})

onUnmounted(() => {
  window.removeEventListener('click', onDocClick)
})

function souResponsavel(t) {
  return t.assignees.some((a) => a.membership_id === myId.value)
}

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
  } catch (err) {
    erro.value = err.message
  }
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>{{ title }}</h1>
        <p class="subtitle">{{ subtitle }}</p>
      </div>
      <button v-if="!archived" id="btn-nova-tarefa" class="btn btn-primary" @click="formAberto = true">
        <Plus :size="16" />
        Nova Tarefa
      </button>
    </div>

    <div v-if="archived" class="alert-info" style="margin-bottom: 1rem">Projeto arquivado: não aceita novas tarefas.</div>
    <div v-if="erro" class="alert-error" style="margin-bottom: 1rem">{{ erro }}</div>

    <div class="filters" role="tablist">
      <button
        class="filter"
        :class="{ active: filtro === 'all' }"
        @click="filtro = 'all'"
      >
        Todas ({{ store.tasks.length }})
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
    <div v-else-if="visiveis.length === 0" class="empty-box">
      <h3>Nenhuma tarefa aqui</h3>
      <p>Use "+ Nova Tarefa" para criar a primeira.</p>
    </div>

    <ul v-else class="task-list">
      <li v-for="t in visiveis" :key="t.id" class="task-card" @click="abertaId = t.id">
        <div class="task-main">
          <h3>{{ t.title }}</h3>
          <div class="meta">
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

    <TaskFormModal :is-open="formAberto" :project-id="projectId" @close="formAberto = false" />
    <TaskDetailModal
      v-if="aberta"
      :task="aberta"
      :scope-project-id="projectId"
      @close="abertaId = null"
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
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}

.filter:hover {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.06);
}

.filter.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
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
  cursor: pointer;
}

.task-card:hover {
  border-color: var(--border-color-hover);
  background: var(--bg-card-hover);
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
  background: rgba(255, 255, 255, 0.08);
}

.task-dropdown-menu {
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

.menu-item-danger {
  color: #f87171;
}

.menu-item-danger:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}
</style>
