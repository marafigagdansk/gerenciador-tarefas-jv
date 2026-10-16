<script setup>
import { ref } from 'vue'
import { useCompanyStore } from '../stores/company'
import { X, Trash2, AlertTriangle } from 'lucide-vue-next'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  project: { type: Object, default: null },
})

const emit = defineEmits(['close', 'deleted'])

const company = useCompanyStore()
const erro = ref('')
const excluindo = ref(false)

async function confirmarExclusao() {
  if (!props.project) return
  erro.value = ''
  excluindo.value = true
  try {
    await company.deleteProject(props.project.id)
    emit('deleted', props.project.id)
    emit('close')
  } catch (err) {
    erro.value = err.message || 'Erro ao excluir o projeto.'
  } finally {
    excluindo.value = false
  }
}

function fechar() {
  if (excluindo.value) return
  erro.value = ''
  emit('close')
}
</script>

<template>
  <div v-if="isOpen && project" class="modal-backdrop" @click.self="fechar">
    <div class="modal-box delete-modal-box">
      <div class="modal-header">
        <div class="modal-title-with-icon">
          <div class="icon-warning-wrapper">
            <AlertTriangle :size="20" />
          </div>
          <h3>Excluir Projeto</h3>
        </div>
        <button class="btn-icon" :disabled="excluindo" @click="fechar" aria-label="Fechar">
          <X :size="20" />
        </button>
      </div>

      <div class="modal-body">
        <div v-if="erro" class="alert-error" style="margin-bottom: 1rem">{{ erro }}</div>

        <p class="delete-description">
          Tem certeza de que deseja excluir permanentemente o projeto
          <strong class="project-highlight">"{{ project.name }}"</strong>?
        </p>

        <div class="danger-warning-box">
          <p>
            <strong>Atenção:</strong> Esta ação é irreversível. Todas as tarefas,
            sub-tarefas e permissões vinculadas a este projeto serão excluídas definitivamente.
          </p>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" :disabled="excluindo" @click="fechar">
            Cancelar
          </button>
          <button
            id="btn-confirmar-exclusao-projeto"
            type="button"
            class="btn btn-danger"
            :disabled="excluindo"
            @click="confirmarExclusao"
          >
            <Trash2 :size="15" />
            {{ excluindo ? 'Excluindo...' : 'Sim, Excluir Projeto' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.delete-modal-box {
  max-width: 480px;
}

.modal-title-with-icon {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.icon-warning-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: #FEF2F2;
  color: #B91C1C;
  border: 1px solid #FECACA;
  flex-shrink: 0;
}

.delete-description {
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text-main);
  margin-bottom: 1rem;
}

.project-highlight {
  color: var(--text-main);
  font-weight: 700;
  word-break: break-word;
}

.danger-warning-box {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: var(--radius-sm);
  padding: 0.85rem 1rem;
  font-size: 0.85rem;
  line-height: 1.45;
  color: #B91C1C;
}

.danger-warning-box strong {
  color: #991B1B;
}
</style>
