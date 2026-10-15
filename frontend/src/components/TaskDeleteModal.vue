<script setup>
import { ref } from 'vue'
import { useTaskStore } from '../stores/task'
import { X, Trash2, AlertTriangle } from 'lucide-vue-next'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  task: { type: Object, default: null },
})

const emit = defineEmits(['close', 'deleted'])

const store = useTaskStore()
const erro = ref('')
const excluindo = ref(false)

async function confirmarExclusao() {
  if (!props.task) return
  erro.value = ''
  excluindo.value = true
  try {
    await store.deleteTask(props.task.id)
    emit('deleted', props.task.id)
    emit('close')
  } catch (err) {
    erro.value = err.message || 'Erro ao excluir a tarefa.'
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
  <div v-if="isOpen && task" class="modal-backdrop" @click.self="fechar">
    <div class="modal-box delete-modal-box">
      <div class="modal-header">
        <div class="modal-title-with-icon">
          <div class="icon-warning-wrapper">
            <AlertTriangle :size="20" />
          </div>
          <h3>Excluir Tarefa</h3>
        </div>
        <button class="btn-icon" :disabled="excluindo" @click="fechar" aria-label="Fechar">
          <X :size="20" />
        </button>
      </div>

      <div class="modal-body">
        <div v-if="erro" class="alert-error" style="margin-bottom: 1rem">{{ erro }}</div>

        <p class="delete-description">
          Tem certeza de que deseja excluir permanentemente a tarefa
          <strong class="task-highlight">"{{ task.title }}"</strong>?
        </p>

        <div class="danger-warning-box">
          <p>
            <strong>Atenção:</strong> Esta ação é irreversível. Qualquer histórico da tarefa,
            incluindo sub-tarefas, responsáveis e alterações, será apagado definitivamente.
          </p>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" :disabled="excluindo" @click="fechar">
            Cancelar
          </button>
          <button
            type="button"
            class="btn btn-danger"
            :disabled="excluindo"
            @click="confirmarExclusao"
          >
            <Trash2 :size="15" />
            {{ excluindo ? 'Excluindo...' : 'Sim, Excluir Tarefa' }}
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
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  flex-shrink: 0;
}

.delete-description {
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text-main);
  margin-bottom: 1rem;
}

.task-highlight {
  color: #fff;
  font-weight: 600;
  word-break: break-word;
}

.danger-warning-box {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.25);
  border-radius: var(--radius-sm);
  padding: 0.85rem 1rem;
  font-size: 0.85rem;
  line-height: 1.45;
  color: #fca5a5;
}

.danger-warning-box strong {
  color: #f87171;
}
</style>
