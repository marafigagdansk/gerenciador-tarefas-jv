<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { useCompanyStore } from '../stores/company'
import TaskWorkspace from '../components/TaskWorkspace.vue'
import ProjectAccessModal from '../components/ProjectAccessModal.vue'

const route = useRoute()
const router = useRouter()
const company = useCompanyStore()

const project = ref(null)
const erro = ref('')
const acessoAberto = ref(false)

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
</script>

<template>
  <div v-if="project" :key="project.id">
    <div v-if="erro" class="alert-error" style="margin-bottom: 1rem">{{ erro }}</div>

    <div v-if="company.isMasterInCurrentCompany" class="project-tools">
      <button id="btn-acesso-projeto" class="btn btn-secondary btn-sm" @click="acessoAberto = true">Gerenciar acesso</button>
      <button id="btn-arquivar-projeto" class="btn btn-secondary btn-sm" @click="alternarArquivo">
        {{ project.status === 'active' ? 'Arquivar projeto' : 'Reativar projeto' }}
      </button>
    </div>

    <TaskWorkspace
      :project-id="project.id"
      :title="project.name"
      :subtitle="project.description || 'Tarefas deste projeto.'"
      :archived="project.status === 'archived'"
    />

    <ProjectAccessModal :is-open="acessoAberto" :project-id="project.id" @close="acessoAberto = false" />
  </div>
  <p v-else-if="!erro" class="loading-state">Carregando projeto...</p>
</template>

<style scoped>
.project-tools {
  display: flex;
  gap: 0.6rem;
  justify-content: flex-end;
  margin-bottom: 0.75rem;
}
</style>
