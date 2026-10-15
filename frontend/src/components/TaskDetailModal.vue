<script setup>
import { ref, computed, watch } from 'vue'
import { useTaskStore } from '../stores/task'
import { useCompanyStore } from '../stores/company'
import { STATUS_LABELS, PRIORITY_LABELS, formatDate } from '../api'
import { Calendar, CalendarOff, X, CheckCircle, UserPlus, Check, Plus, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  task: { type: Object, required: true },
  scopeProjectId: { type: Number, default: null },
})
const emit = defineEmits(['close', 'request-delete'])

const store = useTaskStore()
const company = useCompanyStore()

const erro = ref('')
const salvando = ref(false)
const novaSub = ref('')

const edit = ref({
  title: props.task.title,
  description: props.task.description,
  priority: props.task.priority,
  dueDate: props.task.due_date || '',
})

watch(() => props.task, (t) => {
  if (!t) return
  edit.value = {
    title: t.title,
    description: t.description,
    priority: t.priority,
    dueDate: t.due_date || '',
  }
})

const isMaster = computed(() => company.isMasterInCurrentCompany)
const myId = computed(() => company.activeMembership?.id ?? null)
const podeExcluir = computed(() => props.task.created_by_membership_id === myId.value || isMaster.value)
const assigned = computed(() => props.task.assignees.some((a) => a.membership_id === myId.value))
const canChangeStatus = computed(() => isMaster.value || assigned.value)
const activeMembers = computed(() => company.members.filter((m) => m.is_active))
const openProjects = computed(() =>
  company.projects.filter((p) => p.status === 'active' || p.id === props.task.project_id)
)
const assigneeIds = computed(() => props.task.assignees.map((a) => a.membership_id))
const dirty = computed(() =>
  edit.value.title !== props.task.title ||
  edit.value.description !== props.task.description ||
  edit.value.priority !== props.task.priority ||
  (edit.value.dueDate || null) !== (props.task.due_date || null)
)

async function run(fn) {
  erro.value = ''
  salvando.value = true
  try {
    await fn()
  } catch (err) {
    erro.value = err.message
  } finally {
    salvando.value = false
  }
}

const salvarCampos = () => run(() => store.updateTask(props.task.id, {
  title: edit.value.title,
  description: edit.value.description,
  priority: edit.value.priority,
  due_date: edit.value.dueDate || null,
}, props.scopeProjectId))
const mudarStatus = (e) => run(() => store.updateTask(props.task.id, { status: e.target.value }, props.scopeProjectId))
const concluir = () => run(() => store.updateTask(props.task.id, { status: 'done' }, props.scopeProjectId))
const pegar = () => run(() => store.claimTask(props.task.id, props.scopeProjectId))
const moverProjeto = (e) => {
  const v = e.target.value
  return run(() => store.updateTask(props.task.id, { project_id: v === '' ? null : Number(v) }, props.scopeProjectId))
}
const alternarResp = (mid, checked) => {
  const ids = checked ? [...assigneeIds.value, mid] : assigneeIds.value.filter((i) => i !== mid)
  return run(() => store.setAssignees(props.task.id, ids, props.scopeProjectId))
}
const addSub = () => run(async () => {
  if (!novaSub.value.trim()) return
  await store.addSubtask(props.task.id, novaSub.value, props.scopeProjectId)
  novaSub.value = ''
})
const toggleSub = (s, e) => run(() => store.toggleSubtask(props.task.id, s.id, e.target.checked, props.scopeProjectId))
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal-box modal-lg">
      <div class="modal-header">
        <h3>Detalhes da Tarefa</h3>
        <div class="header-actions">
          <button
            v-if="podeExcluir"
            type="button"
            class="btn-icon btn-header-danger"
            title="Excluir tarefa"
            aria-label="Excluir tarefa"
            @click="emit('request-delete', task)"
          >
            <Trash2 :size="18" />
          </button>
          <button class="btn-icon" @click="emit('close')" aria-label="Fechar">
            <X :size="20" />
          </button>
        </div>
      </div>

      <div class="modal-body">
        <div v-if="erro" class="alert-error">{{ erro }}</div>

        <!-- (1) Título, descrição, status e projeto -->
        <section class="block">
          <template v-if="isMaster">
            <div class="form-group">
              <label for="det-titulo">Título</label>
              <input id="det-titulo" v-model="edit.title" type="text" />
            </div>
            <div class="form-group">
              <label for="det-desc">Descrição</label>
              <textarea id="det-desc" v-model="edit.description" />
            </div>
            <div class="form-group">
              <label for="det-prioridade">Prioridade</label>
              <select id="det-prioridade" v-model="edit.priority">
                <option v-for="(label, key) in PRIORITY_LABELS" :key="key" :value="key">{{ label }}</option>
              </select>
            </div>
            <div class="form-group">
              <div class="label-with-action">
                <label for="det-data-conclusao">Data de Conclusão (opcional)</label>
                <button
                  v-if="edit.dueDate"
                  type="button"
                  class="btn-text-action"
                  @click="edit.dueDate = ''"
                >
                  Limpar (indefinida)
                </button>
              </div>
              <input id="det-data-conclusao" v-model="edit.dueDate" type="date" />
              <span class="hint">Deixe em branco para data de conclusão indefinida.</span>
            </div>
            <div>
              <button id="btn-salvar-campos" class="btn btn-secondary btn-sm" :disabled="!dirty || salvando" @click="salvarCampos">
                Salvar alterações
              </button>
            </div>
          </template>
          <template v-else>
            <h2 class="task-title">{{ task.title }}</h2>
            <p class="task-desc">{{ task.description || 'Sem descrição.' }}</p>
            <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
              <span class="badge" :class="`badge-${task.priority}`">Prioridade {{ PRIORITY_LABELS[task.priority] }}</span>
              <span v-if="task.due_date" class="badge badge-due">
                <Calendar :size="13" />
                Conclusão: {{ formatDate(task.due_date) }}
              </span>
              <span v-else class="badge badge-muted">
                <CalendarOff :size="13" />
                Data indefinida
              </span>
            </div>
          </template>

          <div class="grid-2">
            <div class="form-group">
              <label for="det-status">Status</label>
              <select id="det-status" :value="task.status" :disabled="!canChangeStatus || salvando" @change="mudarStatus">
                <option v-for="(label, key) in STATUS_LABELS" :key="key" :value="key">{{ label }}</option>
              </select>
              <p v-if="!canChangeStatus" class="hint">Pegue a tarefa para alterar o status.</p>
            </div>
            <div class="form-group">
              <label for="det-projeto">Projeto</label>
              <select v-if="isMaster" id="det-projeto" :value="task.project_id ?? ''" :disabled="salvando" @change="moverProjeto">
                <option value="">Tarefa Geral (sem projeto)</option>
                <option v-for="p in openProjects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
              <span v-else class="badge badge-muted fit">{{ task.project_name || 'Tarefa Geral' }}</span>
            </div>
          </div>

          <p class="hint">Criada por {{ task.created_by_name }}</p>

          <div v-if="canChangeStatus && task.status !== 'done'">
            <button id="btn-concluir" class="btn btn-primary btn-sm" :disabled="salvando" @click="concluir">
              <CheckCircle :size="14" />
              Concluir Tarefa
            </button>
          </div>
        </section>

        <!-- (2) Responsáveis -->
        <section class="block">
          <div class="block-head">
            <h4>Responsáveis</h4>
            <button v-if="!assigned" id="btn-pegar-tarefa" class="btn btn-primary btn-sm" :disabled="salvando" @click="pegar">
              <UserPlus :size="14" />
              Pegar Tarefa
            </button>
            <button v-else class="btn btn-secondary btn-sm" disabled>
              <Check :size="14" />
              Já atribuído
            </button>
          </div>
          <ul v-if="task.assignees.length" class="plain-list">
            <li v-for="a in task.assignees" :key="a.membership_id">{{ a.name }}</li>
          </ul>
          <p v-else class="hint">Nenhum responsável ainda.</p>

          <div v-if="isMaster" class="form-group">
            <span class="form-label">Gerenciar responsáveis</span>
            <div class="check-list">
              <label v-for="m in activeMembers" :key="m.id" class="check-row">
                <input
                  type="checkbox"
                  :checked="assigneeIds.includes(m.id)"
                  :disabled="salvando"
                  @change="alternarResp(m.id, $event.target.checked)"
                />
                {{ m.name }}
              </label>
            </div>
          </div>
        </section>

        <!-- (3) Sub-tarefas -->
        <section class="block">
          <h4>Sub-tarefas</h4>
          <ul v-if="task.subtasks.length" class="plain-list">
            <li v-for="s in task.subtasks" :key="s.id" class="sub-row">
              <label class="check-row">
                <input type="checkbox" :checked="s.is_completed" :disabled="!assigned || salvando" @change="toggleSub(s, $event)" />
                <span :class="{ done: s.is_completed }">{{ s.title }}</span>
              </label>
              <span class="hint">Criado por: {{ s.created_by_name }}</span>
            </li>
          </ul>
          <p v-else class="hint">Nenhuma sub-tarefa.</p>

          <form class="sub-form" @submit.prevent="addSub">
            <input
              id="det-nova-sub"
              v-model="novaSub"
              type="text"
              placeholder="Nova sub-tarefa"
              :disabled="!assigned || salvando"
              autocomplete="off"
            />
            <button id="btn-add-sub" type="submit" class="btn btn-secondary btn-sm" :disabled="!assigned || salvando">
              <Plus :size="14" />
              Adicionar
            </button>
          </form>
          <p v-if="!assigned" class="hint">Clique em "Pegar Tarefa" para criar ou marcar sub-tarefas.</p>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.block {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding-bottom: 1.1rem;
  border-bottom: 1px solid var(--border-color);
}

.block:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h4 {
  font-size: 0.95rem;
}

.task-title {
  font-size: 1.25rem;
  overflow-wrap: anywhere;
}

.task-desc {
  color: var(--text-muted);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.fit {
  align-self: flex-start;
}

.plain-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sub-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.done {
  text-decoration: line-through;
  color: var(--text-muted);
}

.sub-form {
  display: flex;
  gap: 0.5rem;
}

@media (max-width: 600px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-header-danger {
  color: #f87171;
}

.btn-header-danger:hover {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.15);
}
</style>
