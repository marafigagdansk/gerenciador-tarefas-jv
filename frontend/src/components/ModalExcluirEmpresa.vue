<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useCompanyStore } from '../stores/company'
import { X, Trash2, AlertTriangle } from 'lucide-vue-next'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  empresa: { type: Object, default: null },
})

const emit = defineEmits(['close', 'deleted'])

const auth = useAuthStore()
const companyStore = useCompanyStore()

const erro = ref('')
const excluindo = ref(false)

async function confirmarExclusao() {
  if (!props.empresa) return
  erro.value = ''
  excluindo.value = true
  try {
    const id = props.empresa.company_id
    await auth.deleteCompany(id)

    if (companyStore.companyId === id) {
      companyStore.reset()
    }

    emit('deleted', id)
    emit('close')
  } catch (err) {
    erro.value = err.message || 'Erro ao excluir a empresa.'
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
  <div v-if="isOpen && empresa" class="modal-backdrop" @click.self="fechar">
    <div class="modal-box delete-empresa-box">
      <div class="modal-header">
        <div class="modal-title-with-icon">
          <div class="icon-danger-wrapper">
            <AlertTriangle :size="20" />
          </div>
          <h3>Excluir Empresa</h3>
        </div>
        <button class="btn-icon" :disabled="excluindo" @click="fechar" aria-label="Fechar">
          <X :size="20" />
        </button>
      </div>

      <div class="modal-body">
        <div v-if="erro" class="alert-error" style="margin-bottom: 1rem">{{ erro }}</div>

        <p class="delete-description">
          Você tem certeza de que deseja excluir permanentemente a empresa
          <strong class="empresa-highlight">"{{ empresa.company_name }}"</strong>?
        </p>

        <div class="danger-warning-box">
          <p class="danger-title">
            <AlertTriangle :size="15" />
            <strong>Aviso Crítico de Perda Total de Dados:</strong>
          </p>
          <p>
            Esta ação é <strong>irreversível</strong>. Todos os dados desta empresa serão
            <strong>definitivamente apagados</strong>, incluindo:
          </p>
          <ul class="danger-list">
            <li>Todas as tarefas e sub-tarefas cadastradas</li>
            <li>Todos os projetos e suas configurações de visibilidade</li>
            <li>Todos os vínculos, papéis e permissões de membros da equipe</li>
            <li>Todo o histórico de registros e atividades da empresa</li>
          </ul>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" :disabled="excluindo" @click="fechar">
            Cancelar
          </button>
          <button
            id="btn-confirmar-excluir-empresa"
            type="button"
            class="btn btn-danger"
            :disabled="excluindo"
            @click="confirmarExclusao"
          >
            <Trash2 :size="15" />
            {{ excluindo ? 'Excluindo...' : 'Sim, Excluir Empresa' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.delete-empresa-box {
  max-width: 520px;
}

.modal-title-with-icon {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.icon-danger-wrapper {
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

.empresa-highlight {
  color: #fff;
  font-weight: 600;
  word-break: break-word;
}

.danger-warning-box {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.25);
  border-radius: var(--radius-sm);
  padding: 0.9rem 1rem;
  font-size: 0.85rem;
  line-height: 1.45;
  color: #fca5a5;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.danger-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #f87171;
}

.danger-list {
  margin: 0;
  padding-left: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: #fecaca;
}
</style>
