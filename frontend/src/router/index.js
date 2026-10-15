import { createRouter, createWebHistory } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'
import { useCompanyStore } from '../stores/company'

import SetupView from '../views/SetupView.vue'
import LoginView from '../views/LoginView.vue'
import CompanyLobbyView from '../views/CompanyLobbyView.vue'
import CompanyWorkspaceLayout from '../views/CompanyWorkspaceLayout.vue'
import TasksView from '../views/TasksView.vue'
import ProjectView from '../views/ProjectView.vue'
import MembersView from '../views/MembersView.vue'

const routes = [
  { path: '/', redirect: '/companies' },
  { path: '/setup', name: 'setup', component: SetupView, meta: { public: true } },
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/companies', name: 'companies', component: CompanyLobbyView },
  {
    path: '/companies/:companyId(\\d+)',
    component: CompanyWorkspaceLayout,
    children: [
      { path: '', redirect: (to) => `/companies/${to.params.companyId}/tasks` },
      { path: 'tasks', name: 'tasks', component: TasksView },
      { path: 'projects/:projectId(\\d+)', name: 'project', component: ProjectView },
      { path: 'members', name: 'members', component: MembersView, meta: { masterOnly: true } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/companies' },
]

const router = createRouter({ history: createWebHistory(), routes })

let needsSetup = null

router.beforeEach(async (to) => {
  // 1. Banco vazio: tudo redireciona para /setup. Depois do 1º usuário, /setup fica bloqueada.
  if (needsSetup !== false) {
    try {
      needsSetup = (await api('/setup/status')).needs_setup
    } catch {
      needsSetup = null
    }
  }
  if (needsSetup === true) return to.name === 'setup' ? true : { name: 'setup' }
  if (to.name === 'setup') return { name: 'login' }

  const auth = useAuthStore()

  // 2. Autenticação global
  if (!auth.isAuthenticated) return to.meta.public ? true : { name: 'login' }
  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
      return to.meta.public ? true : { name: 'login' }
    }
  }
  if (to.name === 'login') return { name: 'companies' }

  // 3. Workspace da empresa: carrega activeMembership e aplica RBAC de rota
  const companyId = to.params.companyId
  const company = useCompanyStore()
  if (companyId) {
    if (company.companyId !== Number(companyId)) {
      try {
        await company.load(companyId)
      } catch {
        company.reset()
        return { name: 'companies' }
      }
    }
    if (to.meta.masterOnly && !company.isMasterInCurrentCompany) {
      return { name: 'tasks', params: { companyId } }
    }
  } else if (company.companyId) {
    company.reset()
  }
  return true
})

export default router
