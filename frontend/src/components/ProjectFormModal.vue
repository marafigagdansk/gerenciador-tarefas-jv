<script setup>
import { ref, computed, watch } from 'vue'
import { useCompanyStore } from '../stores/company'

const props = defineProps({ isOpen: Boolean })
const emit = defineEmits(['close', 'created'])

const company = useCompanyStore()
const name = ref('')
const description = ref('')
const visibleTo = ref([])
const erro = ref('')
const carregando = ref(false)

const collaborators = computed(() =>
  company.members.filter((m) => m.role === 'collaborator' && m.is_active)
)

watch(() => props.isOpen, (open) => {
  if (open) {
    name.value = ''
    description.value = ''
    visibleTo.value = []
    erro.value = ''
  }
})

async function salvar() {
  erro.value = ''
  carregando.value = true
  try {
    const p = await company.createProject({
      name: name.value,
      description: description.value,
      visible_to: visibleTo.value,
    })
    emit('created', p)
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
        <h3>Novo Projeto</h3>
        <button class="btn-icon" @click="emit('close')" aria-label="Fechar">&times;</button>
      </div>
      <form @submit.prevent="salvar" class="modal-body">
        <div v-if="erro" class="alert-error">{{ erro }}</div>
        <div class="form-group">
          <label for="proj-nome">Nome</label>
          <input id="proj-nome" v-model="name" type="text" required autocomplete="off" />
        </div>
        <div class="form-group">
          <label for="proj-desc">Descrição</label>
          <textarea id="proj-desc" v-model="description" />
        </div>
        <div class="form-group">
          <span class="form-label">Colaboradores com acesso</span>
          <div class="check-list">
            <label v-for="m in collaborators" :key="m.id" class="check-row">
              <input type="checkbox" :value="m.id" v-model="visibleTo" />
              {{ m.name }}
            </label>
            <span v-if="collaborators.length === 0" class="hint">Nenhum colaborador cadastrado. Masters veem todos os projetos.</span>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="emit('close')" :disabled="carregando">Cancelar</button>
          <button id="btn-salvar-projeto" type="submit" class="btn btn-primary" :disabled="carregando">
            {{ carregando ? 'Criando...' : 'Criar projeto' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
