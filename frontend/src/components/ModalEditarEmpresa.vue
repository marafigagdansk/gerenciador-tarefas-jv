<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useCompanyStore } from '../stores/company'
import { maskDoc } from '../api'
import { X, Building2 } from 'lucide-vue-next'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  empresa: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])

const auth = useAuthStore()
const companyStore = useCompanyStore()

const name = ref('')
const cnpj = ref('')
const erro = ref('')
const salvando = ref(false)

watch(
  () => props.empresa,
  (val) => {
    if (val) {
      name.value = val.company_name || ''
      cnpj.value = maskDoc(val.cnpj || '')
      erro.value = ''
    }
  },
  { immediate: true }
)

function onDoc(e) {
  cnpj.value = maskDoc(e.target.value)
}

async function salvar() {
  if (!props.empresa) return
  erro.value = ''
  salvando.value = true
  try {
    await auth.updateCompany(props.empresa.company_id, {
      name: name.value,
      cnpj: cnpj.value,
    })

    if (companyStore.companyId === props.empresa.company_id && companyStore.company) {
      companyStore.company.name = name.value
      companyStore.company.cnpj = cnpj.value.replace(/\D/g, '')
    }

    emit('saved')
    emit('close')
  } catch (err) {
    erro.value = err.message || 'Erro ao atualizar dados da empresa.'
  } finally {
    salvando.value = false
  }
}

function fechar() {
  if (salvando.value) return
  erro.value = ''
  emit('close')
}
</script>

<template>
  <div v-if="isOpen && empresa" class="modal-backdrop" @click.self="fechar">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title-with-icon">
          <div class="icon-header-wrapper">
            <Building2 :size="18" />
          </div>
          <h3>Editar Empresa</h3>
        </div>
        <button class="btn-icon" :disabled="salvando" @click="fechar" aria-label="Fechar">
          <X :size="20" />
        </button>
      </div>

      <form @submit.prevent="salvar" class="modal-body">
        <div v-if="erro" class="alert-error">{{ erro }}</div>

        <div class="form-group">
          <label for="edit-empresa-nome">Nome da empresa</label>
          <input
            id="edit-empresa-nome"
            v-model="name"
            type="text"
            required
            autocomplete="off"
            placeholder="Nome fantasia ou razão social"
          />
        </div>

        <div class="form-group">
          <label for="edit-empresa-doc">CNPJ (ou CPF)</label>
          <input
            id="edit-empresa-doc"
            :value="cnpj"
            @input="onDoc"
            type="text"
            required
            autocomplete="off"
            placeholder="00.000.000/0000-00"
          />
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" :disabled="salvando" @click="fechar">
            Cancelar
          </button>
          <button id="btn-salvar-edicao-empresa" type="submit" class="btn btn-primary" :disabled="salvando">
            {{ salvando ? 'Salvando...' : 'Salvar alterações' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-title-with-icon {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.icon-header-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
}
</style>
