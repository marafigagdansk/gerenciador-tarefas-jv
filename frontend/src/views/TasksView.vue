<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '../stores/company'
import { useTaskStore } from '../stores/task'
import { useNotificationStore } from '../stores/notification'
import { formatDate, STATUS_LABELS } from '../api'
import {
  Activity,
  Flame,
  AlertTriangle,
  Clock,
  Target,
  CheckCircle,
  Folder,
  Star,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from 'lucide-vue-next'
import TaskWorkspace from '../components/TaskWorkspace.vue'
import TaskDetailModal from '../components/TaskDetailModal.vue'

const router = useRouter()
const company = useCompanyStore()
const taskStore = useTaskStore()
const notifStore = useNotificationStore()

const painelExpandido = ref(true)
const atualizandoRadar = ref(false)
const selectedTaskModal = ref(null)

const criticalTasks = computed(() => notifStore.radarData.critical_tasks || [])
const todayTasks = computed(() => notifStore.radarData.today_tasks || [])
const importantProjects = computed(() => notifStore.radarData.important_projects || [])

async function recarregarRadar() {
  if (!company.companyId) return
  atualizandoRadar.value = true
  try {
    await notifStore.fetchOverviewRadar(company.companyId)
  } finally {
    atualizandoRadar.value = false
  }
}

function abrirDetalhes(task) {
  selectedTaskModal.value = task
}

function fecharModalDetalhes() {
  selectedTaskModal.value = null
  if (company.companyId) {
    notifStore.fetchOverviewRadar(company.companyId)
    taskStore.fetchTasks(null)
  }
}

async function concluirRapido(task) {
  try {
    await taskStore.updateTask(task.id, { status: 'done' }, null)
    if (company.companyId) {
      await notifStore.fetchOverviewRadar(company.companyId)
    }
  } catch (err) {
    console.warn('Erro ao concluir tarefa rapidamente:', err)
  }
}

function irParaProjeto(projId) {
  router.push({
    name: 'project',
    params: { companyId: company.companyId, projectId: projId },
  })
}

function healthLabel(status) {
  switch (status) {
    case 'critical':
      return { text: 'Crítico', cls: 'health-critical', icon: AlertTriangle }
    case 'warning':
      return { text: 'Atenção', cls: 'health-warning', icon: AlertCircle }
    default:
      return { text: 'Saudável', cls: 'health-healthy', icon: CheckCircle2 }
  }
}
</script>

<template>
  <div class="tasks-view-container">
    <!-- Painel de Atenção e Prioridades (Retrátil) -->
    <section class="priority-radar-panel" :class="{ 'is-collapsed': !painelExpandido }">
      <div class="radar-header">
        <div class="radar-title-wrap">
          <div class="radar-icon-badge">
            <Activity :size="18" />
          </div>
          <div>
            <h3 class="radar-title">Painel de Atenção e Prioridades</h3>
            <p class="radar-subtitle">
              {{ criticalTasks.length }} crítica(s) • {{ todayTasks.length }} foco de hoje • {{ importantProjects.length }} projeto(s) acompanhado(s)
            </p>
          </div>
        </div>

        <div class="radar-actions">
          <button
            type="button"
            class="btn-radar-tool"
            :class="{ 'is-spinning': atualizandoRadar }"
            title="Atualizar painel"
            aria-label="Atualizar painel"
            @click="recarregarRadar"
          >
            <RefreshCw :size="15" />
          </button>
          <button
            type="button"
            class="btn-radar-toggle"
            :title="painelExpandido ? 'Recolher painel' : 'Expandir painel'"
            @click="painelExpandido = !painelExpandido"
          >
            <span class="toggle-text">{{ painelExpandido ? 'Recolher' : 'Expandir' }}</span>
            <ChevronUp v-if="painelExpandido" :size="16" />
            <ChevronDown v-else :size="16" />
          </button>
        </div>
      </div>

      <!-- Corpo com as 3 Colunas Responsivas -->
      <transition name="panel-expand">
        <div v-show="painelExpandido" class="radar-grid">
          <!-- Coluna 1: Tarefas Críticas & Atrasos -->
          <div class="radar-col col-critical">
            <div class="col-head">
              <div class="col-title-group">
                <Flame :size="16" class="col-icon text-danger" />
                <h4>Tarefas Críticas & Atrasos</h4>
              </div>
              <span class="count-pill badge-danger">{{ criticalTasks.length }}</span>
            </div>

            <div class="col-body custom-scrollbar">
              <div
                v-for="task in criticalTasks"
                :key="'crit-' + task.id"
                class="radar-task-card card-critical"
                @click="abrirDetalhes(task)"
              >
                <div class="card-badges-row">
                  <span v-if="task.is_overdue" class="badge-alert-pill badge-alert-danger">
                    <AlertTriangle :size="12" />
                    Atrasada há {{ task.days_overdue || 1 }}d
                  </span>
                  <span v-else-if="task.due_today" class="badge-alert-pill badge-alert-warning">
                    <Clock :size="12" />
                    Vence Hoje!
                  </span>
                  <span v-else class="badge-alert-pill badge-alert-danger">
                    <Flame :size="12" />
                    Urgente
                  </span>

                  <span v-if="task.project_name" class="proj-tag" :title="task.project_name">
                    <Folder :size="11" />
                    {{ task.project_name }}
                  </span>
                </div>

                <h5 class="task-card-title">{{ task.title }}</h5>

                <div class="card-footer-row">
                  <span v-if="task.due_date" class="meta-date">
                    Prazo: {{ formatDate(task.due_date) }}
                  </span>
                  <button
                    type="button"
                    class="btn-card-action"
                    title="Ver detalhes"
                    @click.stop="abrirDetalhes(task)"
                  >
                    Detalhes
                    <ExternalLink :size="12" />
                  </button>
                </div>
              </div>

              <div v-if="criticalTasks.length === 0" class="col-empty-state">
                <CheckCircle2 :size="24" class="empty-ok-icon" />
                <p>Nenhuma tarefa atrasada ou crítica. Excelente!</p>
              </div>
            </div>
          </div>

          <!-- Coluna 2: Tarefas do Dia & Em Andamento -->
          <div class="radar-col col-today">
            <div class="col-head">
              <div class="col-title-group">
                <Target :size="16" class="col-icon text-primary" />
                <h4>Tarefas do Dia & Foco</h4>
              </div>
              <span class="count-pill badge-primary">{{ todayTasks.length }}</span>
            </div>

            <div class="col-body custom-scrollbar">
              <div
                v-for="task in todayTasks"
                :key="'today-' + task.id"
                class="radar-task-card card-today"
                @click="abrirDetalhes(task)"
              >
                <div class="card-badges-row">
                  <span class="badge-status-pill" :class="`status-${task.status}`">
                    {{ STATUS_LABELS[task.status] || task.status }}
                  </span>
                  <span v-if="task.project_name" class="proj-tag" :title="task.project_name">
                    <Folder :size="11" />
                    {{ task.project_name }}
                  </span>
                </div>

                <h5 class="task-card-title">{{ task.title }}</h5>

                <div class="card-footer-row">
                  <span v-if="task.due_date" class="meta-date">
                    {{ formatDate(task.due_date) }}
                  </span>
                  <span v-else class="meta-date">Em andamento</span>

                  <button
                    type="button"
                    class="btn-quick-done"
                    title="Marcar como concluída"
                    @click.stop="concluirRapido(task)"
                  >
                    <CheckCircle :size="14" />
                    Concluir
                  </button>
                </div>
              </div>

              <div v-if="todayTasks.length === 0" class="col-empty-state">
                <Sparkles :size="24" class="empty-ok-icon" />
                <p>Nenhuma tarefa em foco no momento.</p>
              </div>
            </div>
          </div>

          <!-- Coluna 3: Projetos Mais Importantes & Saúde -->
          <div class="radar-col col-projects">
            <div class="col-head">
              <div class="col-title-group">
                <Folder :size="16" class="col-icon text-indigo" />
                <h4>Projetos & Saúde</h4>
              </div>
              <span class="count-pill badge-neutral">{{ importantProjects.length }}</span>
            </div>

            <div class="col-body custom-scrollbar">
              <div
                v-for="p in importantProjects"
                :key="'proj-' + p.id"
                class="radar-project-card"
                :class="{ 'is-featured': p.is_important }"
                @click="irParaProjeto(p.id)"
              >
                <div class="proj-card-head">
                  <div class="proj-title-wrap">
                    <Star
                      v-if="p.is_important"
                      :size="14"
                      fill="#EAB308"
                      color="#CA8A04"
                      class="star-badge"
                    />
                    <strong class="proj-name" :title="p.name">{{ p.name }}</strong>
                  </div>

                  <span
                    class="health-badge"
                    :class="healthLabel(p.health_status).cls"
                    :title="`Status de saúde: ${healthLabel(p.health_status).text}`"
                  >
                    <component :is="healthLabel(p.health_status).icon" :size="12" />
                    {{ healthLabel(p.health_status).text }}
                  </span>
                </div>

                <!-- Barra de Progresso do Projeto -->
                <div class="proj-progress-section">
                  <div class="proj-progress-info">
                    <span class="prog-text">{{ p.completed_tasks }}/{{ p.total_tasks }} tarefas</span>
                    <strong class="prog-pct">{{ p.progress_percent }}%</strong>
                  </div>
                  <div class="radar-progress-bar">
                    <span
                      class="progress-fill"
                      :class="`fill-${p.health_status}`"
                      :style="{ width: p.progress_percent + '%' }"
                    ></span>
                  </div>
                </div>

                <!-- Alerta de atraso se houver -->
                <div v-if="p.overdue_tasks > 0" class="proj-overdue-alert">
                  <AlertTriangle :size="12" />
                  <span>{{ p.overdue_tasks }} tarefa(s) atrasada(s)</span>
                </div>
              </div>

              <div v-if="importantProjects.length === 0" class="col-empty-state">
                <Folder :size="24" class="empty-ok-icon" />
                <p>Nenhum projeto cadastrado.</p>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </section>

    <!-- Workspace Principal de Tarefas -->
    <TaskWorkspace
      :project-id="null"
      kanban
      title="Tarefas Gerais"
      subtitle="Visíveis para todos os membros da empresa. Segure a alça de um card para reordenar ou mover entre colunas."
    />

    <!-- Modal de Detalhes da Tarefa quando acionado via Radar -->
    <TaskDetailModal
      v-if="selectedTaskModal"
      :task="selectedTaskModal"
      :scope-project-id="selectedTaskModal.project_id"
      @close="fecharModalDetalhes"
    />
  </div>
</template>

<style scoped>
.tasks-view-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* ---------- Painel de Atenção e Prioridades ---------- */
.priority-radar-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: all 0.2s ease;
}

.radar-header {
  padding: 1rem 1.25rem;
  background: #FAF9F8;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.priority-radar-panel.is-collapsed .radar-header {
  border-bottom: none;
}

.radar-title-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.radar-icon-badge {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: #F0FDFA;
  color: #0F766E;
  border: 1px solid #CCFBF1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-title {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.radar-subtitle {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin: 0.15rem 0 0;
}

.radar-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-radar-tool {
  background: #FFFFFF;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 0.4rem 0.6rem;
  cursor: pointer;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.btn-radar-tool:hover {
  background: #F5F5F4;
  color: var(--text-main);
}

.btn-radar-tool.is-spinning svg {
  animation: spin 1s infinite linear;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.btn-radar-toggle {
  background: #FFFFFF;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 0.4rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-main);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 0.15s ease;
}

.btn-radar-toggle:hover {
  background: #F5F5F4;
}

/* ---------- Grid das 3 Colunas ---------- */
.radar-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  divide-x: 1px solid var(--border-color);
  background: #FFFFFF;
}

.radar-col {
  padding: 1.1rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  border-right: 1px solid var(--border-color);
}

.radar-col:last-child {
  border-right: none;
}

.col-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed var(--border-color);
}

.col-title-group {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.col-title-group h4 {
  font-size: 0.86rem;
  font-weight: 700;
  margin: 0;
  color: var(--text-main);
}

.text-danger { color: #DC2626; }
.text-primary { color: #0F766E; }
.text-indigo { color: #4F46E5; }

.count-pill {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 999px;
}

.badge-danger {
  background: #FEE2E2;
  color: #B91C1C;
}

.badge-primary {
  background: #CCFBF1;
  color: #0F766E;
}

.badge-neutral {
  background: #F5F5F4;
  color: #44403C;
}

.col-body {
  max-height: 310px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding-right: 0.2rem;
}

/* ---------- Cards de Tarefas no Radar ---------- */
.radar-task-card {
  background: #FAF9F8;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.85rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  transition: all 0.15s ease;
}

.radar-task-card:hover {
  background: #FFFFFF;
  border-color: #CBD5E1;
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.card-critical {
  border-left: 3px solid #EF4444;
}

.card-today {
  border-left: 3px solid #3B82F6;
}

.card-badges-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.badge-alert-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.badge-alert-danger {
  background: #FEE2E2;
  color: #991B1B;
}

.badge-alert-warning {
  background: #FEF3C7;
  color: #92400E;
}

.badge-status-pill {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: #E0E7FF;
  color: #3730A3;
}

.badge-status-pill.status-in_progress {
  background: #DBEAFE;
  color: #1E40AF;
}

.proj-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  color: var(--text-muted);
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-card-title {
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--text-main);
  margin: 0;
  line-height: 1.3;
}

.card-footer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.15rem;
}

.meta-date {
  font-size: 0.72rem;
  color: var(--text-subtle);
}

.btn-card-action {
  background: none;
  border: none;
  font-size: 0.75rem;
  color: var(--primary);
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0;
}

.btn-card-action:hover {
  text-decoration: underline;
}

.btn-quick-done {
  background: #ECFDF5;
  border: 1px solid #A7F3D0;
  color: #065F46;
  font-size: 0.74rem;
  font-weight: 600;
  border-radius: 4px;
  padding: 2px 7px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  transition: all 0.15s ease;
}

.btn-quick-done:hover {
  background: #059669;
  color: #FFFFFF;
}

/* ---------- Cards de Projetos no Radar ---------- */
.radar-project-card {
  background: #FAF9F8;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.85rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  transition: all 0.15s ease;
}

.radar-project-card:hover {
  background: #FFFFFF;
  border-color: #CBD5E1;
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.radar-project-card.is-featured {
  border-left: 3px solid #EAB308;
}

.proj-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.proj-title-wrap {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
  flex: 1;
}

.proj-name {
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.star-badge {
  flex-shrink: 0;
}

.health-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  flex-shrink: 0;
}

.health-critical {
  background: #FEE2E2;
  color: #991B1B;
}

.health-warning {
  background: #FEF3C7;
  color: #92400E;
}

.health-healthy {
  background: #DCFCE7;
  color: #166534;
}

.proj-progress-section {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.proj-progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.prog-pct {
  font-weight: 700;
  color: var(--text-main);
}

.radar-progress-bar {
  height: 6px;
  background: #E5E7EB;
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s ease;
}

.fill-critical { background: #EF4444; }
.fill-warning { background: #F59E0B; }
.fill-healthy { background: #10B981; }

.proj-overdue-alert {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #B91C1C;
}

/* Estados vazios */
.col-empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-subtle);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.empty-ok-icon {
  opacity: 0.5;
  color: #10B981;
}

.col-empty-state p {
  font-size: 0.8rem;
  margin: 0;
}

/* Responsividade */
@media (max-width: 1050px) {
  .radar-grid {
    grid-template-columns: 1fr;
    divide-x: none;
    row-gap: 1rem;
  }
  .radar-col {
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 1.25rem;
  }
  .radar-col:last-child {
    border-bottom: none;
  }
}
</style>
