<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { STATUS_LABELS, PRIORITY_LABELS, formatDate } from '../api'
import { GripVertical, Calendar, CalendarOff, UserPlus, CheckSquare, FolderGit2 } from 'lucide-vue-next'

const props = defineProps({
  tasks: { type: Array, required: true },
  myId: { type: Number, default: null },
  isMaster: Boolean,
})
const emit = defineEmits(['open', 'claim', 'move', 'denied'])

const COLUMN_COLORS = {
  todo: '#475569',
  in_progress: '#1D4ED8',
  blocked: '#B91C1C',
  done: '#15803D',
}

const columns = computed(() =>
  Object.keys(STATUS_LABELS).map((status) => ({
    status,
    label: STATUS_LABELS[status],
    color: COLUMN_COLORS[status] || '#94a3b8',
    tasks: props.tasks
      .filter((t) => t.status === status)
      .sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id),
  }))
)

// ---------- Arrastar e soltar (HTML5 nativo, somente pela alça) ----------
const handleTaskId = ref(null) // card liberado para arrastar (mousedown na alça)
const draggingId = ref(null) // card sendo arrastado (para esmaecer)
const overStatus = ref(null)
const overIndex = ref(0)
let dragInfo = null

function resetDrag() {
  dragInfo = null
  handleTaskId.value = null
  draggingId.value = null
  overStatus.value = null
  overIndex.value = 0
}

function onDragStart(e, t) {
  dragInfo = { id: t.id, status: t.status }
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(t.id))
  // Adia o esmaecimento para que a "sombra" do arraste seja capturada com o card normal
  setTimeout(() => {
    if (dragInfo) draggingId.value = t.id
  }, 0)
}

function onDragOver(e, status) {
  if (!dragInfo) return
  e.preventDefault()
  e.dataTransfer.dropEffect = 'move'
  const cards = [...e.currentTarget.querySelectorAll(':scope > .kb-card')].filter(
    (el) => Number(el.dataset.id) !== dragInfo.id
  )
  let idx = 0
  for (const el of cards) {
    const r = el.getBoundingClientRect()
    if (e.clientY > r.top + r.height / 2) idx++
    else break
  }
  overStatus.value = status
  overIndex.value = idx
}

function onDragLeave(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) overStatus.value = null
}

function canChangeStatus(t) {
  return props.isMaster || t.assignees.some((a) => a.membership_id === props.myId)
}

function onDrop(e, status) {
  if (!dragInfo) return
  const info = dragInfo
  const at = overStatus.value === status ? overIndex.value : null
  resetDrag()

  const task = props.tasks.find((t) => t.id === info.id)
  if (!task) return
  if (info.status !== status && !canChangeStatus(task)) {
    emit('denied', 'Você precisa estar atribuído à tarefa para movê-la de coluna. Clique em "Pegar".')
    return
  }

  const col = columns.value.find((c) => c.status === status)
  const current = col.tasks.map((t) => t.id)
  const ids = current.filter((id) => id !== info.id)
  ids.splice(at ?? ids.length, 0, info.id)

  const mesmaOrdem = info.status === status && ids.length === current.length && ids.every((id, i) => id === current[i])
  if (mesmaOrdem) return
  emit('move', { status, ids })
}

// Colunas + indicador de posição de soltura (linha entre os cards)
function columnItems(col) {
  const items = []
  let visible = 0
  const showIndicator = (i) => dragInfo && overStatus.value === col.status && overIndex.value === i
  for (const t of col.tasks) {
    const isDragged = draggingId.value === t.id
    if (!isDragged) {
      if (showIndicator(visible)) items.push({ key: 'ind', indicator: true })
      visible++
    }
    items.push({ key: t.id, task: t })
  }
  if (showIndicator(visible)) items.push({ key: 'ind', indicator: true })
  return items
}

onMounted(() => window.addEventListener('mouseup', onWindowMouseUp))
onUnmounted(() => window.removeEventListener('mouseup', onWindowMouseUp))

function onWindowMouseUp() {
  // Clique sem arrastar: desabilita o draggable do card
  if (!dragInfo) handleTaskId.value = null
}

// ---------- Apresentação do card ----------
function hojeStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function isAtrasada(task) {
  if (!task.due_date || task.status === 'done') return false
  return task.due_date.split('T')[0] < hojeStr()
}

function souResponsavel(t) {
  return t.assignees.some((a) => a.membership_id === props.myId)
}

function progresso(t) {
  if (!t.subtasks.length) return null
  return Math.round((t.subtasks.filter((s) => s.is_completed).length / t.subtasks.length) * 100)
}

function initials(name) {
  const p = (name || '?').trim().split(/\s+/)
  return ((p[0][0] || '') + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase()
}

function firstName(name) {
  return (name || '').trim().split(/\s+/)[0]
}
</script>

<template>
  <div class="kb-board">
    <section
      v-for="col in columns"
      :key="col.status"
      class="kb-col"
      :class="{ 'kb-col-over': overStatus === col.status }"
      :style="{ '--col-color': col.color }"
    >
      <header class="kb-col-header">
        <span class="kb-dot"></span>
        <h2>{{ col.label }}</h2>
        <span class="kb-count">{{ col.tasks.length }}</span>
      </header>

      <ul
        class="kb-list"
        @dragover="onDragOver($event, col.status)"
        @dragleave="onDragLeave"
        @drop.prevent="onDrop($event, col.status)"
      >
        <template v-for="item in columnItems(col)" :key="item.key">
          <li v-if="item.indicator" class="kb-indicator" aria-hidden="true"></li>
          <li
            v-else
            class="kb-card"
            :class="{ 'kb-dragging': draggingId === item.task.id }"
            :data-id="item.task.id"
            :draggable="handleTaskId === item.task.id"
            @dragstart="onDragStart($event, item.task)"
            @dragend="resetDrag"
            @click="emit('open', item.task)"
          >
            <div class="kb-card-top">
              <span
                class="kb-handle"
                role="img"
                title="Segure e arraste para organizar"
                aria-label="Arrastar tarefa"
                @mousedown.stop="handleTaskId = item.task.id"
                @click.stop
              >
                <GripVertical :size="16" />
              </span>
              <h3 class="kb-title">{{ item.task.title }}</h3>
            </div>

            <div v-if="item.task.project_name" class="kb-project-tag" :title="`Projeto: ${item.task.project_name}`">
              <FolderGit2 :size="12" />
              <span class="kb-project-name">{{ item.task.project_name }}</span>
            </div>

            <div class="kb-meta">
              <span class="badge" :class="`badge-${item.task.priority}`">{{ PRIORITY_LABELS[item.task.priority] }}</span>
              <span
                v-if="item.task.due_date"
                class="badge"
                :class="isAtrasada(item.task) ? 'badge-overdue' : 'badge-due'"
                :title="isAtrasada(item.task) ? 'Tarefa com prazo expirado' : 'Prazo de conclusão'"
              >
                <Calendar :size="12" />
                {{ formatDate(item.task.due_date) }}
              </span>
              <span v-else class="badge badge-muted" title="Sem prazo definido">
                <CalendarOff :size="12" />
                Sem prazo
              </span>
            </div>

            <div v-if="item.task.subtasks.length" class="kb-progress-wrap">
              <div class="kb-progress" :title="`${progresso(item.task)}% das sub-tarefas concluídas`">
                <span :style="{ width: progresso(item.task) + '%' }"></span>
              </div>
              <span class="kb-sub-count">
                <CheckSquare :size="12" />
                {{ item.task.subtasks.filter((s) => s.is_completed).length }}/{{ item.task.subtasks.length }}
              </span>
            </div>

            <footer class="kb-card-footer">
              <div class="kb-assignees">
                <template v-if="item.task.assignees.length">
                  <span
                    v-for="a in item.task.assignees.slice(0, 3)"
                    :key="a.membership_id"
                    class="kb-avatar"
                    :title="a.name"
                  >{{ initials(a.name) }}</span>
                  <span class="kb-assignee-name">
                    {{ firstName(item.task.assignees[0].name) }}<template v-if="item.task.assignees.length > 1"> +{{ item.task.assignees.length - 1 }}</template>
                  </span>
                </template>
                <span v-else class="kb-assignee-name">Sem responsável</span>
              </div>
              <button
                v-if="!souResponsavel(item.task)"
                type="button"
                class="btn btn-primary btn-sm kb-claim"
                @click.stop="emit('claim', item.task)"
              >
                <UserPlus :size="13" />
                Pegar
              </button>
            </footer>
          </li>
        </template>

        <li v-if="col.tasks.length === 0 && overStatus !== col.status" class="kb-empty">Arraste tarefas aqui</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.kb-board {
  display: grid;
  grid-template-columns: repeat(4, minmax(260px, 1fr));
  gap: 1.25rem;
  align-items: start;
  overflow-x: auto;
  padding-bottom: 0.75rem;
}

.kb-col {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 0.75rem;
  background: #EBEAE8;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: border-color 0.15s ease, background 0.15s ease;
}

.kb-col-over {
  border-color: var(--col-color);
  background: #E2E0DC;
}

.kb-col-header {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.7rem;
  margin-bottom: 0.75rem;
  background: #FFFFFF;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04);
}

.kb-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--col-color);
  flex-shrink: 0;
}

.kb-col-header h2 {
  flex: 1;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-main);
}

.kb-count {
  min-width: 24px;
  padding: 0.05rem 0.5rem;
  text-align: center;
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-muted);
  background: #F5F5F4;
  border: 1px solid var(--border-color);
  border-radius: 999px;
}

.kb-list {
  list-style: none;
  min-height: 120px;
  max-height: calc(100vh - 290px);
  overflow-y: auto;
  padding: 0.3rem 0.15rem 0.3rem 0;
}

.kb-card {
  margin-bottom: 0.6rem;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease, opacity 0.15s ease;
}

.kb-card:hover {
  border-color: #D6D3D1;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
  background: var(--bg-card);
}

.kb-card[draggable='true'] {
  cursor: grabbing;
}

.kb-dragging {
  opacity: 0.35;
}

.kb-card-top {
  display: flex;
  align-items: flex-start;
  gap: 0.35rem;
}

.kb-handle {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 24px;
  margin: -2px 0 0 -4px;
  padding: 0;
  color: var(--text-subtle);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.15s ease;
}

.kb-handle:hover {
  color: var(--text-main);
  background: #F5F5F4;
}

.kb-handle:active {
  cursor: grabbing;
}

.kb-title {
  font-size: 0.94rem;
  font-weight: 700;
  line-height: 1.35;
  color: var(--text-main);
  overflow-wrap: anywhere;
}

.kb-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.kb-progress-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.kb-progress {
  flex: 1;
  height: 5px;
  background: #E7E5E4;
  border-radius: 999px;
  overflow: hidden;
}

.kb-progress span {
  display: block;
  height: 100%;
  background: #0F766E;
  border-radius: 999px;
}

.kb-sub-count {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted);
}

.kb-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.kb-assignees {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-width: 0;
}

.kb-avatar {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  margin-left: -6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.62rem;
  font-weight: 800;
  color: #0F766E;
  background: #F0FDFA;
  border: 1px solid #99F6E4;
  border-radius: 50%;
}

.kb-avatar:first-child {
  margin-left: 0;
}

.kb-assignee-name {
  margin-left: 0.2rem;
  font-size: 0.78rem;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-claim {
  flex-shrink: 0;
  padding: 0.3rem 0.65rem;
  font-size: 0.76rem;
}

.kb-empty {
  padding: 2.5rem 0.75rem;
  text-align: center;
  font-size: 0.82rem;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.45);
  border: 1px dashed #D6D3D1;
  border-radius: var(--radius-md);
}

/* Indicador de posição: altura zero para não deslocar os cards durante o arraste */
.kb-indicator {
  position: relative;
  height: 0;
  list-style: none;
}

.kb-indicator::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: -5px;
  height: 3px;
  border-radius: 2px;
  background: var(--col-color);
  box-shadow: 0 0 6px var(--col-color);
}

.kb-project-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #0F766E;
  background: #F0FDFA;
  border: 1px solid #99F6E4;
  border-radius: var(--radius-sm);
  padding: 0.18rem 0.45rem;
  max-width: 100%;
  margin-top: 0.1rem;
  margin-bottom: 0.15rem;
  width: fit-content;
}

.kb-project-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
