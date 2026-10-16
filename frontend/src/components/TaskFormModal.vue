<script setup>
import { ref, computed, watch } from 'vue'
import { useTaskStore } from '../stores/task'
import { useCompanyStore } from '../stores/company'
import { PRIORITY_LABELS } from '../api'
import { X, Plus } from 'lucide-vue-next'
import CustomDatePicker from './CustomDatePicker.vue'
import CustomSelect from './CustomSelect.vue'

const props = defineProps({ isOpen: Boolean, projectId: { type: Number, default: null } })
const emit = defineEmits(['close'])

const store = useTaskStore()
const company = useCompanyStore()

const title = ref('')
const description = ref('')
const priority = ref('medium')
const dueDate = ref('')
const targetProject = ref(null)
const assignees = ref([])
const erro = ref('')
const carregando = ref(false)

const isMaster = computed(() => company.isMasterInCurrentCompany)
const activeMembers = computed(() => company.members.filter((m) => m.is_active))
const openProjects = computed(() =>
  company.projects.filter((p) => p.status === 'active' && (isMaster.value || p.can_create_tasks))
)
const autoAssignMe = ref(false)

const priorityOptions = computed(() =>
  Object.keys(PRIORITY_LABELS).map((k) => ({
    value: k,
    label: PRIORITY_LABELS[k],
  }))
)

const projectOptions = computed(() => [
  { value: null, label: 'Tarefa Geral (sem projeto)' },
  ...openProjects.value.map((p) => ({ value: p.id, label: p.name })),
])

watch(() => props.isOpen, (open) => {
  if (!open) return
  title.value = ''
  description.value = ''
  priority.value = 'medium'
  dueDate.value = ''
  targetProject.value = props.projectId
  assignees.value = []
  autoAssignMe.value = false
  erro.value = ''
})

async function salvar() {
  erro.value = ''
  carregando.value = true
  try {
    const payload = {
      title: title.value,
      description: description.value,
      priority: priority.value,
      due_date: dueDate.value || null,
      project_id: targetProject.value,
    }
    if (isMaster.value) {
      payload.assignee_ids = assignees.value
    } else {
      if (targetProject.value === null || autoAssignMe.value) {
        payload.assignee_ids = [company.activeMembership?.id].filter(Boolean)
      } else {
        payload.assignee_ids = []
      }
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
        <button class="btn-icon" @click="emit('close')" aria-label="Fechar">
          <X :size="20" />
        </button>
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
          <CustomSelect
            id="tarefa-prioridade"
            v-model="priority"
            :options="priorityOptions"
            type="priority"
          />
        </div>
        <div class="form-group">
          <label for="tarefa-data-conclusao">Data de Conclusão (opcional)</label>
          <CustomDatePicker
            id="tarefa-data-conclusao"
            v-model="dueDate"
            placeholder="Definir data de conclusão"
          />
          <span class="hint">Caso não informada, a tarefa ficará com data indefinida.</span>
        </div>

        <template v-if="isMaster">
          <div class="form-group">
            <label for="tarefa-projeto">Projeto</label>
            <CustomSelect
              id="tarefa-projeto"
              v-model="targetProject"
              :options="projectOptions"
            />
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
        <template v-else>
          <div v-if="openProjects.length > 0" class="form-group">
            <label for="tarefa-projeto">Projeto</label>
            <CustomSelect
              id="tarefa-projeto"
              v-model="targetProject"
              :options="projectOptions"
            />
          </div>
          <div v-if="targetProject" class="form-group">
            <label class="check-row">
              <input type="checkbox" v-model="autoAssignMe" />
              <span>Pegar esta tarefa para mim agora</span>
            </label>
            <span class="hint">Se desmarcado, a tarefa ficará disponível para qualquer membro do projeto pegar.</span>
          </div>
          <p v-if="!targetProject" class="alert-info">
            Esta tarefa será criada em <strong>Tarefas Gerais</strong> (visível apenas para você) e atribuída a você.
          </p>
          <p v-else class="alert-info">
            Esta tarefa ficará vinculada ao <strong>Projeto</strong> e visível para todos os membros atribuídos poderem pegar a tarefa.
          </p>
        </template>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="emit('close')" :disabled="carregando">Cancelar</button>
          <button id="btn-salvar-tarefa" type="submit" class="btn btn-primary" :disabled="carregando">
            <Plus :size="16" v-if="!carregando" />
            {{ carregando ? 'Criando...' : 'Criar tarefa' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
