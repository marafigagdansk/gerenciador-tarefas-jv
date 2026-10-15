<script setup>
import { ref, computed, watch } from 'vue'
import { useTaskStore } from '../stores/task'
import { useCompanyStore } from '../stores/company'
import { PRIORITY_LABELS } from '../api'

const props = defineProps({ isOpen: Boolean, projectId: { type: Number, default: null } })
const emit = defineEmits(['close'])

const store = useTaskStore()
const company = useCompanyStore()

const title = ref('')
const description = ref('')
const priority = ref('medium')
const targetProject = ref(null)
const assignees = ref([])
const erro = ref('')
const carregando = ref(false)

const isMaster = computed(() => company.isMasterInCurrentCompany)
const activeMembers = computed(() => company.members.filter((m) => m.is_active))
const openProjects = computed(() => company.projects.filter((p) => p.status === 'active'))

watch(() => props.isOpen, (open) => {
  if (!open) return
  title.value = ''
  description.value = ''
  priority.value = 'medium'
  targetProject.value = props.projectId
  assignees.value = []
  erro.value = ''
})

async function salvar() {
  erro.value = ''
  carregando.value = true
  try {
    const payload = { title: title.value, description: description.value, priority: priority.value }
    if (isMaster.value) {
      payload.project_id = targetProject.value
      payload.assignee_ids = assignees.value
    }
    await store.createTask(payload, props.projectId)
    emit('close')
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="emit('close')">
    <div class="modal-box">
      <div class="modal-header">
        <h3>Nova Tarefa</h3>
        <button class="btn-icon" @click="emit('close')" aria-label="Fechar">&times;</button>
      </div>
      <form @submit.prevent="salvar" class="modal-body">
        <div v-if="erro" class="alert-error">{{ erro }}</div>

        <div class="form-group">
          <label for="tarefa-titulo">Título</label>
          <input id="tarefa-titulo" v-model="title" type="text" required autocomplete="off" />
        </div>
        <div class="form-group">
          <label for="tarefa-desc">Descrição</label>
          <textarea id="tarefa-desc" v-model="description" />
        </div>
        <div class="form-group">
          <label for="tarefa-prioridade">Prioridade</label>
          <select id="tarefa-prioridade" v-model="priority">
            <option v-for="(label, key) in PRIORITY_LABELS" :key="key" :value="key">{{ label }}</option>
          </select>
        </div>

        <template v-if="isMaster">
          <div class="form-group">
            <label for="tarefa-projeto">Projeto</label>
            <select id="tarefa-projeto" v-model="targetProject">
              <option :value="null">Tarefa Geral (sem projeto)</option>
              <option v-for="p in openProjects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <span class="form-label">Responsáveis (opcional)</span>
            <div class="check-list">
              <label v-for="m in activeMembers" :key="m.id" class="check-row">
                <input type="checkbox" :value="m.id" v-model="assignees" />
                {{ m.name }}
              </label>
            </div>
          </div>
        </template>
        <p v-else class="alert-info">Esta tarefa será criada como Tarefa Geral e atribuída a você.</p>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="emit('close')" :disabled="carregando">Cancelar</button>
          <button id="btn-salvar-tarefa" type="submit" class="btn btn-primary" :disabled="carregando">
            {{ carregando ? 'Criando...' : 'Criar tarefa' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
