<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'
import { useCompanyStore } from '../stores/company'
import { useNotificationStore } from '../stores/notification'
import { ROLE_LABELS } from '../api'
import {
  ListTodo,
  Folder,
  Users,
  ArrowLeft,
  Plus,
  Bell,
  Star,
  CheckCheck,
  AlertTriangle,
  AlertCircle,
  Info,
  X,
  Sparkles,
  ArrowRight,
} from 'lucide-vue-next'
import ProjectFormModal from '../components/ProjectFormModal.vue'

const company = useCompanyStore()
const notificationStore = useNotificationStore()
const router = useRouter()
const route = useRoute()

const modalProjeto = ref(false)
const menuNotifAberto = ref(false)
const filtroNotif = ref('todas') // 'todas', 'nao_lidas', 'criticas'
const alertaBoasVindasVisivel = ref(false)

onMounted(async () => {
  if (company.companyId) {
    await company.fetchProjects()
    notificationStore.startPolling(company.companyId)
    setTimeout(checarBoasVindas, 600)
  }
})

onUnmounted(() => {
  notificationStore.stopPolling()
})

watch(() => company.companyId, async (newId) => {
  if (newId) {
    await company.fetchProjects(newId)
    notificationStore.startPolling(newId)
    setTimeout(checarBoasVindas, 600)
  } else {
    notificationStore.stopPolling()
  }
})

watch(() => notificationStore.radarData, () => {
  checarBoasVindas()
}, { deep: true })

function checarBoasVindas() {
  if (!company.companyId) return
  const chave = `gt_welcomed_${company.companyId}`
  const jaExibido = sessionStorage.getItem(chave)
  if (!jaExibido) {
    const criticas = notificationStore.radarData.critical_tasks?.length || 0
    const doDia = notificationStore.radarData.today_tasks?.length || 0
    if (criticas > 0 || doDia > 0) {
      alertaBoasVindasVisivel.value = true
    }
  }
}

function dispensarBoasVindas() {
  alertaBoasVindasVisivel.value = false
  if (company.companyId) {
    sessionStorage.setItem(`gt_welcomed_${company.companyId}`, 'true')
  }
}

function verPrioridades() {
  dispensarBoasVindas()
  router.push({ name: 'tasks', params: { companyId: company.companyId } })
}

function projetoCriado(p) {
  router.push({ name: 'project', params: { companyId: company.companyId, projectId: p.id } })
  notificationStore.fetchOverviewRadar(company.companyId)
}

async function toggleImportant(p) {
  try {
    const novoValor = !p.is_important
    await company.updateProject(p.id, { is_important: novoValor })
    notificationStore.fetchOverviewRadar(company.companyId)
  } catch (err) {
    console.warn('Erro ao alternar importância do projeto:', err)
  }
}

const notificacoesFiltradas = computed(() => {
  const lista = notificationStore.notifications || []
  if (filtroNotif.value === 'nao_lidas') {
    return lista.filter((n) => !n.is_read)
  }
  if (filtroNotif.value === 'criticas') {
    return lista.filter((n) => n.severity === 'critical')
  }
  return lista
})

function formatTimeAgo(isoStr) {
  if (!isoStr) return ''
  const date = new Date(isoStr)
  const now = new Date()
  const diffSec = Math.floor((now - date) / 1000)
  if (diffSec < 60) return 'Agora'
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `há ${diffMin} min`
  const diffHours = Math.floor(diffMin / 60)
  if (diffHours < 24) return `há ${diffHours}h`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'Ontem'
  if (diffDays < 7) return `há ${diffDays} dias`
  return date.toLocaleDateString('pt-BR')
}

async function clicarNotificacao(notif) {
  await notificationStore.markAsRead(notif.id)
  menuNotifAberto.value = false
  if (notif.project_id) {
    router.push({
      name: 'project',
      params: { companyId: company.companyId, projectId: notif.project_id },
    })
  } else {
    router.push({
      name: 'tasks',
      params: { companyId: company.companyId },
    })
  }
}

function fecharDropdown(e) {
  if (!e.target.closest('.notif-container')) {
    menuNotifAberto.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', fecharDropdown)
})

onUnmounted(() => {
  window.removeEventListener('click', fecharDropdown)
})
</script>

<template>
  <div v-if="company.company" class="workspace">
    <aside class="sidebar">
      <div class="side-company">
        <div class="side-company-header">
          <h2 :title="company.company.name">{{ company.company.name }}</h2>
          <span v-if="company.activeMembership" class="badge" :class="`badge-${company.activeMembership.role}`">
            {{ ROLE_LABELS[company.activeMembership.role] }}
          </span>
        </div>
        <RouterLink :to="{ name: 'companies' }" id="link-trocar-empresa" class="switch-link">
          <ArrowLeft :size="14" />
          Trocar de empresa
        </RouterLink>
      </div>

      <nav class="side-nav">
        <RouterLink :to="{ name: 'tasks', params: { companyId: company.companyId } }" class="nav-link">
          <span class="nav-label">
            <ListTodo :size="16" />
            Tarefas Gerais
          </span>
        </RouterLink>

        <div class="nav-section">
          <p class="side-label">Projetos</p>
          <RouterLink
            v-for="p in company.projects"
            :key="p.id"
            :to="{ name: 'project', params: { companyId: company.companyId, projectId: p.id } }"
            class="nav-link project-link"
          >
            <span class="nav-label">
              <Folder :size="15" />
              <span class="project-name-text">{{ p.name }}</span>
            </span>
            <div class="project-indicators">
              <button
                v-if="company.isMasterInCurrentCompany"
                type="button"
                class="btn-star"
                :class="{ 'is-active': p.is_important }"
                :title="p.is_important ? 'Projeto importante (clique para desfavoritar)' : 'Marcar como projeto importante'"
                @click.prevent.stop="toggleImportant(p)"
              >
                <Star
                  :size="14"
                  :fill="p.is_important ? '#EAB308' : 'none'"
                  :color="p.is_important ? '#CA8A04' : '#A8A29E'"
                />
              </button>
              <span v-if="p.status === 'archived'" class="badge badge-muted">Arquivado</span>
            </div>
          </RouterLink>
          <p v-if="company.projects.length === 0" class="hint">
            {{ company.isMasterInCurrentCompany ? 'Nenhum projeto criado.' : 'Nenhum projeto liberado para você.' }}
          </p>
          <button
            v-if="company.isMasterInCurrentCompany"
            id="btn-novo-projeto"
            class="btn btn-secondary btn-sm new-project"
            @click="modalProjeto = true"
          >
            <Plus :size="14" />
            Novo Projeto
          </button>
        </div>

        <div v-if="company.isMasterInCurrentCompany" class="nav-section">
          <p class="side-label">Gestão</p>
          <RouterLink :to="{ name: 'members', params: { companyId: company.companyId } }" class="nav-link">
            <span class="nav-label">
              <Users :size="16" />
              Colaboradores
            </span>
          </RouterLink>
        </div>
      </nav>
    </aside>

    <main class="workspace-main">
      <!-- Topbar do Workspace com Sino de Notificações -->
      <div class="workspace-topbar">
        <div class="topbar-left">
          <span class="workspace-crumb">Workspace</span>
          <span class="crumb-separator">/</span>
          <span class="crumb-current">{{ company.company.name }}</span>
        </div>

        <div class="topbar-right">
          <!-- Sino de Notificações -->
          <div class="notif-container">
            <button
              id="btn-notificacoes"
              type="button"
              class="btn-icon btn-bell"
              :class="{ 'has-unread': notificationStore.unreadCount > 0 }"
              title="Notificações"
              aria-label="Notificações"
              @click.stop="menuNotifAberto = !menuNotifAberto"
            >
              <Bell :size="19" />
              <span
                v-if="notificationStore.unreadCount > 0"
                class="notif-badge"
              >
                {{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
              </span>
            </button>

            <!-- Popover de Notificações -->
            <transition name="popover-fade">
              <div v-if="menuNotifAberto" class="notif-popover" @click.stop>
                <div class="notif-popover-header">
                  <div class="notif-header-title">
                    <h4>Notificações</h4>
                    <span v-if="notificationStore.unreadCount > 0" class="badge-count">
                      {{ notificationStore.unreadCount }} não lida{{ notificationStore.unreadCount > 1 ? 's' : '' }}
                    </span>
                  </div>
                  <button
                    v-if="notificationStore.unreadCount > 0"
                    type="button"
                    class="btn-text-action"
                    @click="notificationStore.markAllAsRead(company.companyId)"
                  >
                    <CheckCheck :size="14" />
                    Marcar todas como lidas
                  </button>
                </div>

                <!-- Botão de ativar notificações push no navegador -->
                <div
                  v-if="notificationStore.browserPermission === 'default'"
                  class="notif-permission-banner"
                >
                  <p>Ative os alertas no navegador para ser avisado sobre prazos e atribuições.</p>
                  <button
                    type="button"
                    class="btn btn-primary btn-sm btn-full"
                    @click="notificationStore.requestBrowserPermission()"
                  >
                    Ativar Alertas no Navegador
                  </button>
                </div>

                <!-- Filtros rápidos -->
                <div class="notif-tabs">
                  <button
                    type="button"
                    class="notif-tab"
                    :class="{ 'is-active': filtroNotif === 'todas' }"
                    @click="filtroNotif = 'todas'"
                  >
                    Todas
                  </button>
                  <button
                    type="button"
                    class="notif-tab"
                    :class="{ 'is-active': filtroNotif === 'nao_lidas' }"
                    @click="filtroNotif = 'nao_lidas'"
                  >
                    Não lidas ({{ notificationStore.unreadCount }})
                  </button>
                  <button
                    type="button"
                    class="notif-tab"
                    :class="{ 'is-active': filtroNotif === 'criticas' }"
                    @click="filtroNotif = 'criticas'"
                  >
                    Críticas
                  </button>
                </div>

                <!-- Lista de Notificações -->
                <div class="notif-list">
                  <div
                    v-for="item in notificacoesFiltradas"
                    :key="item.id"
                    class="notif-item"
                    :class="{ 'is-unread': !item.is_read, [`severity-${item.severity}`]: true }"
                    @click="clicarNotificacao(item)"
                  >
                    <div class="notif-icon-col">
                      <span class="severity-icon" :class="`icon-${item.severity}`">
                        <AlertTriangle v-if="item.severity === 'critical'" :size="16" />
                        <AlertCircle v-else-if="item.severity === 'warning'" :size="16" />
                        <Info v-else :size="16" />
                      </span>
                    </div>
                    <div class="notif-content-col">
                      <div class="notif-item-header">
                        <strong class="notif-item-title">{{ item.title }}</strong>
                        <span class="notif-time">{{ formatTimeAgo(item.created_at) }}</span>
                      </div>
                      <p class="notif-message">{{ item.message }}</p>
                    </div>
                    <span v-if="!item.is_read" class="unread-dot"></span>
                  </div>

                  <div v-if="notificacoesFiltradas.length === 0" class="notif-empty">
                    <Bell :size="28" class="empty-icon" />
                    <p>Nenhuma notificação por aqui.</p>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>

      <!-- Alerta de Boas-Vindas / Resumo Executivo ao Entrar -->
      <transition name="slide-down">
        <div v-if="alertaBoasVindasVisivel" class="executive-welcome-banner">
          <div class="welcome-content">
            <div class="welcome-icon">
              <Sparkles :size="20" />
            </div>
            <div class="welcome-text">
              <strong>Atenção ao seu dia</strong>
              <p>
                Você possui
                <span class="hl-critical">
                  {{ notificationStore.radarData.critical_tasks?.length || 0 }} tarefa(s) crítica(s)/atrasada(s)
                </span>
                e
                <span class="hl-today">
                  {{ notificationStore.radarData.today_tasks?.length || 0 }} tarefa(s) em foco para hoje
                </span>.
              </p>
            </div>
          </div>
          <div class="welcome-actions">
            <button type="button" class="btn btn-primary btn-sm" @click="verPrioridades">
              Visualizar
              <ArrowRight :size="14" />
            </button>
            <button
              type="button"
              class="btn-icon btn-dismiss"
              title="Dispensar"
              aria-label="Dispensar alerta"
              @click="dispensarBoasVindas"
            >
              <X :size="16" />
            </button>
          </div>
        </div>
      </transition>

      <RouterView />
    </main>

    <ProjectFormModal :is-open="modalProjeto" @close="modalProjeto = false" @created="projetoCriado" />
  </div>
  <div v-else class="loading-state">
    <p>Carregando workspace da empresa...</p>
  </div>
</template>

<style scoped>
.workspace {
  flex: 1;
  display: grid;
  grid-template-columns: 260px 1fr;
  width: 100%;
  max-width: 100%;
  margin: 0;
}

.sidebar {
  background: #FAF9F8;
  border-right: 1px solid var(--border-color);
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.side-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-subtle);
  margin-bottom: 0.4rem;
}

.side-company-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.side-company-header h2 {
  font-size: 1.15rem;
  margin: 0;
  overflow-wrap: anywhere;
}

.switch-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.8rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary);
  text-decoration: none;
}

.switch-link:hover {
  text-decoration: underline;
  color: var(--primary-hover);
}

.side-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-section {
  margin-top: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.75rem;
  border-radius: var(--radius-sm);
  color: var(--text-main);
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 500;
  border: 1px solid transparent;
  overflow-wrap: anywhere;
  transition: all 0.15s ease;
}

.nav-label {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
  flex: 1;
}

.project-name-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-indicators {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.btn-star {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 3px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: transform 0.15s ease;
}

.btn-star:hover {
  transform: scale(1.15);
}

.nav-link:hover {
  background: #EBEAE8;
}

.nav-link.router-link-active {
  background: #F0FDFA;
  color: #0F766E;
  border-color: #CCFBF1;
  font-weight: 700;
}

.new-project {
  margin-top: 0.5rem;
  align-self: flex-start;
}

.workspace-main {
  padding: 1.25rem 2rem 2rem;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ---------- Topbar ---------- */
.workspace-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--border-color);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.workspace-crumb {
  font-weight: 500;
}

.crumb-separator {
  color: var(--text-subtle);
}

.crumb-current {
  font-weight: 600;
  color: var(--text-main);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* ---------- Sino & Notificações ---------- */
.notif-container {
  position: relative;
}

.btn-bell {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-bell:hover {
  background: #F5F5F4;
  border-color: var(--border-color-hover);
}

.btn-bell.has-unread {
  color: var(--primary);
  border-color: #CCFBF1;
  background: #F0FDFA;
}

.notif-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #DC2626;
  color: #FFFFFF;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 1px 5px;
  min-width: 18px;
  height: 18px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 2px var(--bg-card);
  animation: pulse-badge 2s infinite ease-in-out;
}

@keyframes pulse-badge {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

/* Popover flutuante */
.notif-popover {
  position: absolute;
  top: 46px;
  right: 0;
  width: 390px;
  max-width: 90vw;
  background: #FFFFFF;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-modal);
  z-index: 100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.notif-popover-header {
  padding: 0.85rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  background: #FAF9F8;
}

.notif-header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.notif-header-title h4 {
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
}

.badge-count {
  font-size: 0.72rem;
  font-weight: 600;
  background: #FEE2E2;
  color: #B91C1C;
  padding: 2px 7px;
  border-radius: 999px;
}

.btn-text-action {
  background: none;
  border: none;
  font-size: 0.76rem;
  color: var(--primary);
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.btn-text-action:hover {
  text-decoration: underline;
}

.notif-permission-banner {
  background: #EFF6FF;
  border-bottom: 1px solid #DBEAFE;
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  color: #1E40AF;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-full {
  width: 100%;
}

.notif-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  background: #FAF9F8;
}

.notif-tab {
  flex: 1;
  padding: 0.55rem 0.5rem;
  font-size: 0.78rem;
  font-weight: 600;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.notif-tab:hover {
  color: var(--text-main);
}

.notif-tab.is-active {
  color: var(--primary);
  border-bottom-color: var(--primary);
  background: #FFFFFF;
}

.notif-list {
  max-height: 380px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  position: relative;
  transition: background 0.15s ease;
}

.notif-item:hover {
  background: #F9F9F8;
}

.notif-item.is-unread {
  background: #F0FDF4;
}

.notif-item.is-unread:hover {
  background: #DCFCE7;
}

.notif-item.severity-critical.is-unread {
  background: #FEF2F2;
}

.notif-item.severity-critical.is-unread:hover {
  background: #FEE2E2;
}

.notif-icon-col {
  padding-top: 2px;
}

.severity-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.severity-icon.icon-critical {
  background: #FEE2E2;
  color: #DC2626;
}

.severity-icon.icon-warning {
  background: #FEF3C7;
  color: #D97706;
}

.severity-icon.icon-info {
  background: #DBEAFE;
  color: #2563EB;
}

.notif-content-col {
  flex: 1;
  min-width: 0;
}

.notif-item-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.2rem;
}

.notif-item-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.25;
}

.notif-time {
  font-size: 0.72rem;
  color: var(--text-subtle);
  white-space: nowrap;
}

.notif-message {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.35;
  margin: 0;
  overflow-wrap: anywhere;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  margin-top: 6px;
  flex-shrink: 0;
}

.notif-empty {
  padding: 2.5rem 1.5rem;
  text-align: center;
  color: var(--text-subtle);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.empty-icon {
  opacity: 0.4;
}

/* ---------- Alerta Executivo de Entrada ---------- */
.executive-welcome-banner {
  background: linear-gradient(135deg, #FAF5FF 0%, #F5F3FF 50%, #EFF6FF 100%);
  border: 1px solid #E9D5FF;
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  box-shadow: var(--shadow-sm);
}

.welcome-content {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.welcome-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #8B5CF6;
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.welcome-text strong {
  display: block;
  font-size: 0.95rem;
  color: #5B21B6;
  margin-bottom: 0.15rem;
}

.welcome-text p {
  font-size: 0.86rem;
  color: #4C1D95;
  margin: 0;
}

.hl-critical {
  font-weight: 700;
  color: #B91C1C;
}

.hl-today {
  font-weight: 700;
  color: #1D4ED8;
}

.welcome-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-dismiss {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #6B7280;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: var(--radius-sm);
}

.btn-dismiss:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #111827;
}

/* Transições */
.popover-fade-enter-active,
.popover-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.popover-fade-enter-from,
.popover-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.25s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 800px) {
  .workspace {
    grid-template-columns: 1fr;
  }
  .sidebar {
    border-right: none;
    border-bottom: 1px solid var(--border-color);
  }
  .workspace-main {
    padding: 1rem;
  }
  .notif-popover {
    width: 320px;
  }
}
</style>
