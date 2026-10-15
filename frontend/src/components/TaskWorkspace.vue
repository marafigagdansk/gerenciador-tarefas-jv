<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTaskStore } from '../stores/task'
import { useCompanyStore } from '../stores/company'
import { STATUS_LABELS, PRIORITY_LABELS } from '../api'
import TaskFormModal from './TaskFormModal.vue'
import TaskDetailModal from './TaskDetailModal.vue'

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

const myId = computed(() => company.activeMembership.id)

const visiveis = computed(() =>
  filtro.value === 'all' ? store.tasks : store.tasks.filter((t) => t.status === filtro.value)
)
const aberta = computed(() => store.tasks.find((t) => t.id === abertaId.value) || null)

onMounted(async () => {
  store.tasks = []
  try {
    await store.fetchTasks(props.projectId)
  } catch (err) {
    erro.value = err.message
  }
})

function souResponsavel(t) {
  return t.assignees.some((a) => a.membership_id === myId.value)
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
      <button v-if="!archived" id="btn-nova-tarefa" class="btn btn-primary" @click="formAberto = true">+ Nova Tarefa</button>
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
            <span v-if="t.subtasks.length" class="badge badge-muted">
              Sub-tarefas {{ t.subtasks.filter((s) => s.is_completed).length }}/{{ t.subtasks.length }}
            </span>
          </div>
          <p class="assignees">
            <template v-if="t.assignees.length">Responsáveis: {{ t.assignees.map((a) => a.name).join(', ') }}</template>
            <template v-else>Sem responsável</template>
          </p>
        </div>
        <div class="task-action" @click.stop>
          <button v-if="!souResponsavel(t)" class="btn btn-primary btn-sm" @click="pegar(t)">Pegar Tarefa</button>
          <button v-else class="btn btn-secondary btn-sm" disabled>Já atribuído</button>
        </div>
      </li>
    </ul>

    <TaskFormModal :is-open="formAberto" :project-id="projectId" @close="formAberto = false" />
    <TaskDetailModal v-if="aberta" :task="aberta" :scope-project-id="projectId" @close="abertaId = null" />
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
}
</style>
