<script setup>
import { ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useCompanyStore } from '../stores/company'
import { ROLE_LABELS } from '../api'
import { ListTodo, Folder, Users, ArrowLeft, Plus } from 'lucide-vue-next'
import ProjectFormModal from '../components/ProjectFormModal.vue'

const company = useCompanyStore()
const router = useRouter()
const modalProjeto = ref(false)

function projetoCriado(p) {
  router.push({ name: 'project', params: { companyId: company.companyId, projectId: p.id } })
}
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
            class="nav-link"
          >
            <span class="nav-label">
              <Folder :size="15" />
              {{ p.name }}
            </span>
            <span v-if="p.status === 'archived'" class="badge badge-muted">Arquivado</span>
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
  grid-template-columns: 270px 1fr;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
}

.sidebar {
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
  color: #a5b4fc;
  text-decoration: none;
}

.switch-link:hover {
  text-decoration: underline;
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
  overflow-wrap: anywhere;
}

.nav-label {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.07);
}

.nav-link.router-link-active {
  background: rgba(99, 102, 241, 0.22);
  color: #fff;
  font-weight: 700;
}

.new-project {
  margin-top: 0.5rem;
  align-self: flex-start;
}

.workspace-main {
  padding: 1.5rem 2rem;
  min-width: 0;
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
    padding: 1.25rem 1rem;
  }
}
</style>
